import os
import requests

# ---------------------------
# CONFIG (MANDATORY)
# ---------------------------
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
MODEL_NAME = os.getenv("MODEL_NAME", "rule-based-agent")
TASKS = ["easy", "medium", "hard"]
MAX_STEPS = 20


# ---------------------------
# LOGGING (STRICT FORMAT)
# ---------------------------
def log_start(task):
    print(f"[START] task={task} env=volume_control_env model={MODEL_NAME}", flush=True)


def log_step(step, action, reward, done):
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={str(done).lower()} error=null",
        flush=True,
    )


def log_end(success, steps, score, rewards):
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}",
        flush=True,
    )


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
def choose_action(observation):
    volume = observation.get("current_volume", 0.5)
    loudness = observation.get("current_loudness", 0.5)

    perceived = volume * loudness

    if perceived > 0.7:
        return -1
    elif perceived < 0.3:
        return 1
    else:
        return 0


# ---------------------------
# TASK SCORING
# ---------------------------
def compute_score(task, trajectory):
    if len(trajectory) == 0:
        return 0.0

    if task == "easy":
        good = 0
        for obs in trajectory:
            perceived = obs["current_volume"] * obs["current_loudness"]
            if 0.3 <= perceived <= 0.7:
                good += 1
        return good / len(trajectory)

    elif task == "medium":
        penalty = 0
        for obs in trajectory:
            perceived = obs["current_volume"] * obs["current_loudness"]
            if perceived > 0.8:
                penalty += 1
        return max(0.0, 1 - (penalty / len(trajectory)))

    elif task == "hard":
        score = 0
        prev_volume = None

        for obs in trajectory:
            perceived = obs["current_volume"] * obs["current_loudness"]

            if 0.3 <= perceived <= 0.7:
                score += 0.5

            if prev_volume is not None:
                if abs(obs["current_volume"] - prev_volume) < 0.2:
                    score += 0.5

            prev_volume = obs["current_volume"]

        return min(score / len(trajectory), 1.0)

    return 0.0


# ---------------------------
# HTTP SAFE CALL
# ---------------------------
def safe_post(url, json=None):
    response = requests.post(url, json=json, timeout=5)
    if response.status_code != 200:
        raise Exception(f"HTTP {response.status_code}")
    return response.json()


# ---------------------------
# MAIN LOOP
# ---------------------------
def run_task(task):
    log_start(task)

    rewards = []
    trajectory = []
    steps = 0

    # Reset
    try:
        res = safe_post(f"{API_BASE_URL}/reset")
    except Exception as e:
        print(f"[ERROR] reset_failed error={str(e)}", flush=True)
        log_end(False, 0, 0.0, [])
        return

    obs = extract_observation(res)

    for step in range(1, MAX_STEPS + 1):
        action_value = choose_action(obs)
        action = {"action": {"change": action_value}}

        try:
            res = safe_post(f"{API_BASE_URL}/step", json=action)
        except Exception as e:
            print(f"[ERROR] step_failed error={str(e)}", flush=True)
            log_step(step, action_value, 0.0, True)
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