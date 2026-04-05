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
# SIMPLE AGENT (RULE BASED)
# ---------------------------
def choose_action(observation):
    volume = observation["current_volume"]
    loudness = observation["current_loudness"]

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
        return 1 - (penalty / len(trajectory))

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
# MAIN LOOP
# ---------------------------
def run_task(task):
    log_start(task)

    rewards = []
    trajectory = []
    steps = 0

    # Reset env
    res = requests.post(f"{API_BASE_URL}/reset").json()

    obs = res["observation"]

    for step in range(1, MAX_STEPS + 1):
        action_value = choose_action(obs)

        action = {"action": {"change": action_value}}

        res = requests.post(f"{API_BASE_URL}/step", json=action).json()

        obs = res["observation"]
        reward = res["reward"]
        done = res["done"]

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