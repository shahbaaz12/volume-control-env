# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Volume Control Env Environment Client."""

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from .models import VolumeControlAction, VolumeControlObservation


class VolumeControlEnv(
    EnvClient[VolumeControlAction, VolumeControlObservation, State]
):
    """
    Client for the Volume Control Env Environment.

    This client maintains a persistent WebSocket connection to the environment server,
    enabling efficient multi-step interactions with lower latency.
    Each client instance has its own dedicated environment session on the server.

    This client uses the OpenEnv WebSocket transport, so state is preserved
    across reset(), step(), and state() calls within the same session.
    """

    def _step_payload(self, action: VolumeControlAction) -> Dict:
        """
        Convert VolumeControlAction to JSON payload for step message.

        Args:
            action: VolumeControlAction instance

        Returns:
            Dictionary representation suitable for JSON encoding
        """
        return action.model_dump()

    def _parse_result(self, payload: Dict) -> StepResult[VolumeControlObservation]:
        """
        Parse server response into StepResult[VolumeControlObservation].

        Args:
            payload: JSON response data from server

        Returns:
            StepResult with VolumeControlObservation
        """
        obs_data = payload.get("observation", {})
        observation = VolumeControlObservation(**obs_data)

        return StepResult(
            observation=observation,
            reward=payload.get("reward", observation.reward),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        """
        Parse server response into State object.

        Args:
            payload: JSON response from state request

        Returns:
            State object with episode_id and step_count
        """
        return State(**payload)
