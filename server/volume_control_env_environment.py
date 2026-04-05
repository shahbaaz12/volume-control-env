from openenv.core.env_server.interfaces import Environment

try:
    from ..models import VolumeControlAction, VolumeControlObservation
except ImportError:
    from models import VolumeControlAction, VolumeControlObservation


class VolumeControlEnvironment(Environment):
    def __init__(self):
        self.volume = 0.5
        self.step_count = 0
        self.max_steps = 20
        self.done = False

    def reset(self):
        self.volume = 0.5
        self.step_count = 0
        self.done = False

        return VolumeControlObservation(
            current_volume=self.volume,
            current_loudness=self._get_loudness(),
            reward=0.0,
            done=False
        )

    def step(self, action: VolumeControlAction):
        if self.done:
            return self.reset()

        change = action.change

        self.volume += change * 0.1
        self.volume = max(0.0, min(1.0, self.volume))

        loudness = self._get_loudness()
        perceived = loudness * self.volume

        reward = self._compute_reward(perceived)

        self.step_count += 1
        if self.step_count >= self.max_steps:
            self.done = True

        return VolumeControlObservation(
            current_volume=self.volume,
            current_loudness=loudness,
            reward=reward,
            done=self.done
        )

    def state(self):
        return {
            "volume": self.volume,
            "step_count": self.step_count
        }

    def _get_loudness(self):
        import random
        return random.choice([0.2, 0.3, 0.8, 1.0])

    def _compute_reward(self, perceived):
        if 0.3 <= perceived <= 0.7:
            return 1.0
        elif perceived > 0.7:
            return -1.0
        else:
            return -0.5