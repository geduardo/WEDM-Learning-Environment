# src/edm_env/modules/ignition.py
from __future__ import annotations

import numpy as np

from ..core.module import EDMModule
from ..core.state import EDMState


class IgnitionModule(EDMModule):
    """Stochastic plasma-channel ignition model."""

    def __init__(self, env):
        super().__init__(env)
        self.lambda_cache: dict[float, float] = {}

    # ------------------------------------------------------------------ #
    # Public
    # ------------------------------------------------------------------ #
    def update(self, state: EDMState) -> None:
        target_voltage = state.target_voltage
        peak_current = state.peak_current
        
        #TODO
        ON_time = state.ON_time or 3
        OFF_time = state.OFF_time or 80

        # Physical short-circuit
        if state.wire_position >= state.workpiece_position:
            state.spark_status = [-1, None, 0]
            state.voltage = 0
            state.current = peak_current
            return

        spark_state, spark_loc, spark_dur = state.spark_status

        # Keep an ongoing spark alive
        if spark_state == 1:
            state.spark_status = [1, spark_loc, spark_dur + 1]
            if state.spark_status[2] >= ON_time:
                state.spark_status[0] = -2  # rest
                state.current = 0
                state.voltage = 0
            else:
                state.current = peak_current
                state.voltage = target_voltage * 0.3
            return

        # Rest period bookkeeping
        if spark_state == -2:
            state.spark_status = [-2, None, spark_dur + 1]
            if state.spark_status[2] >= OFF_time + ON_time:
                state.spark_status = [0, None, 0]
                state.voltage = target_voltage
                state.current = 0
            return

        # Idle → maybe ignite
        if spark_state == 0:
            state.voltage = target_voltage
            state.current = 0

            p_ignite = self._cond_prob(state)
            if self.env.np_random.random() < p_ignite:
                spark_loc = self.env.np_random.uniform(0, self.env.workpiece_height)
                state.spark_status = [1, spark_loc, 0]
                state.voltage = target_voltage * 0.3
                state.current = peak_current
            return

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    def _cond_prob(self, state: EDMState) -> float:
        return self.get_lambda(state)

    def get_lambda(self, state: EDMState) -> float:
        if state.wire_position >= state.workpiece_position:
            raise ValueError(
                "get_lambda called with wire_position >= workpiece_position. "
                "Gap must be positive for ignition probability calculation. "
                "This condition should typically be handled as a short-circuit before this point."
            )

        # At this point, state.wire_position < state.workpiece_position,
        # so (state.workpiece_position - state.wire_position) is positive.
        gap = state.workpiece_position - state.wire_position
        
        if gap not in self.lambda_cache:
            self.lambda_cache[gap] = np.log(2) / (0.48 * gap**2 - 3.69 * gap + 14.05)
        
        return self.lambda_cache[gap]
