class BaseTask:
    name = "base"

    def grade(self, trajectory):
        raise NotImplementedError


EPSILON = 0.001


def strict_unit_interval(score):
    return min(max(float(score), EPSILON), 1.0 - EPSILON)


# ---------------------------
# EASY
# ---------------------------
class MaintainComfortEasy(BaseTask):
    name = "easy"

    def grade(self, trajectory):
        good = 0
        total = len(trajectory)

        if total == 0:
            return EPSILON

        for obs in trajectory:
            perceived = obs["current_volume"] * obs["current_loudness"]
            if 0.3 <= perceived <= 0.7:
                good += 1

        return strict_unit_interval(good / total)


# ---------------------------
# MEDIUM
# ---------------------------
class AvoidSpikesMedium(BaseTask):
    name = "medium"

    def grade(self, trajectory):
        penalty = 0
        total = len(trajectory)

        if total == 0:
            return EPSILON

        for obs in trajectory:
            perceived = obs["current_volume"] * obs["current_loudness"]

            if perceived > 0.8:
                penalty += 1

        return strict_unit_interval(1 - (penalty / total))


# ---------------------------
# HARD
# ---------------------------
class StableListeningHard(BaseTask):
    name = "hard"

    def grade(self, trajectory):
        score = 0
        total = len(trajectory)

        if total == 0:
            return EPSILON

        prev_volume = None

        for obs in trajectory:
            perceived = obs["current_volume"] * obs["current_loudness"]

            if 0.3 <= perceived <= 0.7:
                score += 0.5

            if prev_volume is not None:
                if abs(obs["current_volume"] - prev_volume) < 0.2:
                    score += 0.5

            prev_volume = obs["current_volume"]

        return strict_unit_interval(score / total)
