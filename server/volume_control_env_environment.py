from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import VolumeControlAction, VolumeControlObservation
except ImportError:
    from models import VolumeControlAction, VolumeControlObservation


class VolumeControlEnvironment(Environment):
    def __init__(self):
        super().__init__()
        self.episode_id = None
        self.volume = 0.5
        self.step_count = 0
        self.max_steps = 20
        self.done = False

    def reset(self, seed=None, episode_id=None, **kwargs):
        if seed is not None:
            import random
            random.seed(seed)

        self.episode_id = episode_id
        self.volume = 0.5
        self.step_count = 0
        self.done = False

        return VolumeControlObservation(
            current_volume=self.volume,
            current_loudness=self._get_loudness(),
            reward=0.0,
            done=False
        )

    def step(self, action: VolumeControlAction, timeout_s=None, **kwargs):
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

    @property
    def state(self):
        return State(
            episode_id=self.episode_id,
            step_count=self.step_count,
            volume=self.volume,
            done=self.done,
        )

    def _get_loudness(self):
        import random
        return random.choice([0.2, 0.3, 0.8, 1.0])

    def _compute_reward(self, perceived):
        if 0.3 <= perceived <= 0.7:
            return 1.0
        elif perceived > 0.7:
            return 0.0
        else:
            return 0.25
