from pydantic import BaseModel


class VolumeControlObservation(BaseModel):
    current_volume: float
    current_loudness: float

    reward: float
    done: bool


class VolumeControlAction(BaseModel):
    change: int