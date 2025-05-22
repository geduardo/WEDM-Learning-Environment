# src/edm_env/modules/ignition.py
from __future__ import annotations

import numpy as np

from ..core.module import EDMModule
from ..core.state import EDMState
from ..core.state_utils import is_short_circuited


class IgnitionModule(EDMModule):
    """Stochastic plasma-channel ignition model."""

    def __init__(self, env):
        super().__init__(env)
        self.lambda_cache: dict[float, float] = {}

    # ------------------------------------------------------------------ #
    # Public
    # ------------------------------------------------------------------ #
    def update(self, state: EDMState) -> None:
        target_voltage = state.target_voltage or 80.0  # Default values if None
        peak_current = state.peak_current or 300.0  # Default values if None

        ON_time = state.ON_time or 3  # Default values if None
        OFF_time = state.OFF_time or 80  # Default values if None

        short_circuit_active = is_short_circuited(state)
        spark_state, spark_loc, spark_dur = state.spark_status

        # State 1: Ongoing spark (or "ON" period during short circuit)
        if spark_state == 1:
            current_spark_duration = spark_dur + 1
            # Update duration first, spark_loc remains the same for an ongoing spark
            state.spark_status = [1, spark_loc, current_spark_duration]

            if current_spark_duration >= ON_time:
                state.spark_status[0] = -2  # Transition to rest/OFF state
                # spark_dur (current_spark_duration) carries over to state -2
                state.current = 0
                state.voltage = 0
            else:  # Still in ON period
                state.current = peak_current
                if short_circuit_active:
                    state.voltage = 0
                else:
                    state.voltage = target_voltage * 0.3  # Normal sparking voltage
            return

        # State -2: Rest period (or "OFF" period during short circuit)
        if spark_state == -2:
            # spark_dur here is total duration since ON phase started
            current_total_duration = spark_dur + 1
            # spark_loc is None during rest period
            state.spark_status = [-2, None, current_total_duration]  # Update duration

            if current_total_duration >= (ON_time + OFF_time):
                state.spark_status = [0, None, 0]  # Transition to Idle
                state.current = 0
                # Voltage for idle state depends on short circuit
                if short_circuit_active:
                    state.voltage = 0
                else:
                    state.voltage = target_voltage
            else:  # Still in OFF period
                state.current = 0
                state.voltage = 0  # Voltage is 0 during rest
            return

        # State 0: Idle (waiting to ignite or transition to "ON" if shorted)
        if spark_state == 0:
            state.current = 0  # No current when idle (unless it transitions)

            if short_circuit_active:
                # If idle and becomes shorted, behave as if "ignited" into a shorted ON state
                state.spark_status = [
                    1,
                    None,
                    0,
                ]  # Transition to ON state, duration 0, no specific spark_loc
                state.current = peak_current  # Current flows
                state.voltage = 0  # Voltage is 0 due to short
            else:
                # Not short-circuited, attempt normal ignition
                state.voltage = (
                    target_voltage  # Set open voltage before checking ignition
                )
                # _cond_prob will use the current gap, which is positive here.
                p_ignite = self._cond_prob(state)
                if self.env.np_random.random() < p_ignite:
                    new_spark_loc = self.env.np_random.uniform(
                        0, self.env.workpiece_height
                    )
                    state.spark_status = [1, new_spark_loc, 0]  # Ignite, go to ON state
                    state.voltage = target_voltage * 0.3  # Spark voltage
                    state.current = peak_current
                # else: remains idle.
                # state.current is already 0.
                # state.voltage is target_voltage (already set for non-igniting idle).
            return

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    def _cond_prob(self, state: EDMState) -> float:
        # Ensure we don't try to calculate ignition probability if already shorted,
        # as get_lambda might not be defined for non-positive gap.
        # This check is more of a safeguard; primary short-circuit handling is done above.
        if is_short_circuited(state):
            return 0.0  # Or handle as an error/impossible state for ignition
        return self.get_lambda(state)

    def get_lambda(self, state: EDMState) -> float:
        # This check for short-circuit should ideally not be hit if _cond_prob handles it,
        # but it's a good safeguard for direct calls to get_lambda or if logic changes.
        if state.wire_position >= state.workpiece_position:
            # This specific error condition might now be better handled by checking is_short_circuited(state)
            # at the call site of get_lambda or ensuring _cond_prob prevents this call.
            # For now, keeping the original logic, but it's a point for future refinement.
            raise ValueError(
                "get_lambda called when wire_position >= workpiece_position. "
                "Gap must be positive for ignition probability calculation. "
                "This should be handled by is_short_circuited() checks before calling _cond_prob."
            )

        # At this point, state.wire_position < state.workpiece_position,
        # so (state.workpiece_position - state.wire_position) is positive.
        gap = state.workpiece_position - state.wire_position

        if gap not in self.lambda_cache:
            self.lambda_cache[gap] = np.log(2) / (0.48 * gap**2 - 3.69 * gap + 14.05)

        return self.lambda_cache[gap]
