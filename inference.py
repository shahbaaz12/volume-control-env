import json
import os
import re
import requests

try:
    from openai import OpenAI
except ImportError:  # Allows deterministic local fallback if OpenAI is unavailable.
    OpenAI = None

from tasks.tasks import AvoidSpikesMedium, MaintainComfortEasy, StableListeningHard

# ---------------------------
# CONFIG (MANDATORY)
# ---------------------------
API_BASE_URL = os.getenv("API_BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.getenv("HF_TOKEN")
API_KEY = HF_TOKEN or os.getenv("API_KEY")
ENV_BASE_URL = os.getenv(
    "ENV_BASE_URL",
    os.getenv("OPENENV_BASE_URL", os.getenv("SPACE_URL", "http://localhost:8000")),
).rstrip("/")
TASKS = [MaintainComfortEasy(), AvoidSpikesMedium(), StableListeningHard()]
MAX_STEPS = 20
LLM_TIMEOUT_SECONDS = 5.0
HTTP = requests.Session()
if "localhost" in ENV_BASE_URL or "127.0.0.1" in ENV_BASE_URL:
    HTTP.trust_env = False
_llm_client = None
_llm_disabled = False


# ---------------------------
# LOGGING (STRICT FORMAT)
# ---------------------------
def log_start(task):
    print(f"[START] task={task} env=volume_control_env model={MODEL_NAME}", flush=True)


def log_step(step, action, reward, done, error="null"):
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={str(done).lower()} error={error}",
        flush=True,
    )


def log_end(success, steps, score, rewards):
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}",
        flush=True,
    )


def clean_error(error):
    return str(error).replace("\n", " ").replace("\r", " ").replace(" ", "_")[:120]


# ---------------------------
# SAFE OBS PARSER
# ---------------------------
def extract_observation(res):
    if not isinstance(res, dict):
        return {"current_volume": 0.5, "current_loudness": 0.5}

    if "observation" in res:
        return res["observation"]

    return {
        "current_volume": res.get("current_volume", 0.5),
        "current_loudness": res.get("current_loudness", 0.5),
    }


# ---------------------------
# SIMPLE AGENT
# ---------------------------
def rule_based_action(observation):
    volume = observation.get("current_volume", 0.5)
    loudness = observation.get("current_loudness", 0.5)

    perceived = volume * loudness

    if perceived > 0.7:
        return -1
    elif perceived < 0.3:
        return 1
    else:
        return 0


def get_llm_client():
    global _llm_client, _llm_disabled

    if _llm_disabled or _llm_client is not None:
        return _llm_client

    if OpenAI is None or not API_BASE_URL or not API_KEY:
        _llm_disabled = True
        return None

    _llm_client = OpenAI(
        base_url=API_BASE_URL,
        api_key=API_KEY,
        timeout=LLM_TIMEOUT_SECONDS,
    )
    return _llm_client


def parse_action(text):
    match = re.search(r"-?1|0", text or "")
    if not match:
        raise ValueError("No action token found")
    return max(-1, min(1, int(match.group(0))))


def choose_action(observation):
    global _llm_disabled

    fallback = rule_based_action(observation)
    client = get_llm_client()
    if client is None:
        return fallback

    prompt = (
        "You control audio volume. Reply with exactly one integer action: "
        "-1 to lower volume, 0 to keep it, or 1 to raise it. "
        f"Observation JSON: {json.dumps(observation, sort_keys=True)}"
    )

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Return only -1, 0, or 1."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=4,
        )
        return parse_action(response.choices[0].message.content)
    except Exception:
        _llm_disabled = True
        return fallback


# ---------------------------
# TASK SCORING
# ---------------------------
def compute_score(task, trajectory):
    return max(0.0, min(1.0, float(task.grade(trajectory))))


# ---------------------------
# HTTP SAFE CALL
# ---------------------------
def safe_post(url, json=None):
    response = HTTP.post(url, json=json, timeout=5)
    if response.status_code != 200:
        raise Exception(f"HTTP {response.status_code}")
    return response.json()


# ---------------------------
# MAIN LOOP
# ---------------------------
def run_task(task):
    log_start(task.name)

    rewards = []
    trajectory = []
    steps = 0

    # Reset
    try:
        res = safe_post(f"{ENV_BASE_URL}/reset")
    except Exception as e:
        log_step(0, 0, 0.0, True, f"reset_failed:{clean_error(e)}")
        log_end(False, 0, 0.0, [])
        return

    obs = extract_observation(res)

    for step in range(1, MAX_STEPS + 1):
        action_value = choose_action(obs)
        action = {"action": {"change": action_value}}

        try:
            res = safe_post(f"{ENV_BASE_URL}/step", json=action)
        except Exception as e:
            log_step(step, action_value, 0.0, True, f"step_failed:{clean_error(e)}")
            break

        obs = extract_observation(res)
        reward = res.get("reward", 0.0)
        done = res.get("done", False)

        trajectory.append(obs)
        rewards.append(reward)
        steps = step

        log_step(step, action_value, reward, done)

        if done:
            break

    score = compute_score(task, trajectory)
    success = score >= 0.5

    log_end(success, steps, score, rewards)


# ---------------------------
# ENTRY POINT
# ---------------------------
if __name__ == "__main__":
    for task in TASKS:
        run_task(task)
