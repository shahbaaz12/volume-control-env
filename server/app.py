# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.

"""
FastAPI application for the Volume Control Env Environment.
"""

from openenv.core.env_server.http_server import create_app

from server.volume_control_env_environment import VolumeControlEnvironment
from models import VolumeControlAction, VolumeControlObservation

app = create_app(
    VolumeControlEnvironment,
    VolumeControlAction,
    VolumeControlObservation,
    env_name="volume_control_env",
    max_concurrent_envs=1,
)


@app.get("/")
def root():
    return {"status": "healthy", "env": "volume_control_env"}


def main():
    import uvicorn
    uvicorn.run("server.app:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
