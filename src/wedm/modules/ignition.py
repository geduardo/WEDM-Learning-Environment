# src/edm_env/modules/ignition.py
from __future__ import annotations

import json
import numpy as np
from pathlib import Path

from ..core.module import EDMModule
from ..core.state import EDMState
from ..core.state_utils import is_short_circuited


class IgnitionModule(EDMModule):
    """Stochastic plasma-channel ignition model."""

    def __init__(self, env):
        super().__init__(env)
        self.lambda_cache: dict[float, float] = {}
        # Load machine current modes data
        self.currents_data = self._load_currents_data()

        # Cache for efficiency
        self._cached_current_mode: str | None = None
        self._cached_current_value: float = 60.0  # Default to I5 current

    def _load_currents_data(self) -> dict:
        """Load current mode mappings from currents.json."""
        # Get the path relative to this module
        current_dir = Path(__file__).parent
        json_path = current_dir / "currents.json"

        try:
            with open(json_path, "r") as f:
                data = json.load(f)
            return data
        except FileNotFoundError:
            raise FileNotFoundError(f"Could not find currents data file at {json_path}")

    def _get_current_from_mode(self, current_mode: str | None) -> float:
        """Get actual current value from current mode with caching."""
        # Only recalculate if current_mode has changed
        if current_mode != self._cached_current_mode:
            if current_mode is None:
                current_mode = "I5"

            # Get actual current from current mode (0-18 maps to I1-I19)
            if current_mode not in self.currents_data:
                # Fallback to I5 if invalid mode (middle range)
                current_mode = "I5"

            self._cached_current_value = self.currents_data[current_mode]["Current"]
            self._cached_current_mode = current_mode

        return self._cached_current_value

    # ------------------------------------------------------------------ #
    # Public
    # ------------------------------------------------------------------ #
    def update(self, state: EDMState) -> None:
        """Update ignition state with clear, simple logic."""

        # Step 1: Update short circuit detection
        self._update_short_circuit_detection(state)

        # Step 2: Force voltage to 0 if short circuit
        if state.is_short_circuit:
            state.voltage = 0

        # Step 3: Handle state machine
        spark_state = state.spark_status[0]

        if spark_state == 0:
            self._handle_idle_state(state)
        elif spark_state == 1:
            self._handle_spark_state(state)
        elif spark_state == -1:
            self._handle_short_state(state)
        elif spark_state == -2:
            self._handle_rest_state(state)

    def _update_short_circuit_detection(self, state: EDMState) -> None:
        """Update short circuit flag based on gap."""
        gap = max(0.0, state.workpiece_position - state.wire_position)
        state.is_short_circuit = gap < 2.0

    def _handle_idle_state(self, state: EDMState) -> None:
        """Handle idle state (state 0)."""
        state.current = 0

        if state.is_short_circuit:
            # Short circuit during idle → deliver pulse
            state.spark_status = [-1, None, 0]
            state.current = self._get_peak_current(state)
        else:
            # Normal idle → set voltage and check for ignition
            state.voltage = self._get_target_voltage(state)

            if self._should_ignite(state):
                # Start normal spark
                spark_location = self.env.np_random.uniform(
                    0, self.env.workpiece_height
                )
                state.spark_status = [1, spark_location, 0]
                state.voltage = self._get_target_voltage(state) * 0.3
                state.current = self._get_peak_current(state)

    def _handle_spark_state(self, state: EDMState) -> None:
        """Handle active spark state (state 1)."""
        duration = state.spark_status[2] + 1
        state.spark_status[2] = duration

        if duration >= self._get_on_time(state):
            # Spark finished → go to rest
            state.spark_status[0] = -2
            state.current = 0
            if not state.is_short_circuit:
                state.voltage = 0
        else:
            # Continue spark
            state.current = self._get_peak_current(state)
            if not state.is_short_circuit:
                state.voltage = self._get_target_voltage(state) * 0.3

    def _handle_short_state(self, state: EDMState) -> None:
        """Handle short circuit pulse state (state -1)."""
        duration = state.spark_status[2] + 1
        state.spark_status[2] = duration

        if duration >= self._get_on_time(state):
            # Short pulse finished → go to rest
            state.spark_status[0] = -2
            state.current = 0
        else:
            # Continue short pulse
            state.current = self._get_peak_current(state)

    def _handle_rest_state(self, state: EDMState) -> None:
        """Handle rest/off state (state -2)."""
        duration = state.spark_status[2] + 1
        state.spark_status[2] = duration

        total_cycle_time = self._get_on_time(state) + self._get_off_time(state)

        if duration >= total_cycle_time:
            # Rest finished → back to idle
            state.spark_status = [0, None, 0]
            state.current = 0
            if not state.is_short_circuit:
                state.voltage = self._get_target_voltage(state)
        else:
            # Continue rest
            state.current = 0
            if not state.is_short_circuit:
                state.voltage = 0

    def _should_ignite(self, state: EDMState) -> bool:
        """Check if normal ignition should occur."""
        if state.is_short_circuit:
            return False

        ignition_probability = self.get_lambda(state)
        return self.env.np_random.random() < ignition_probability

    def _get_target_voltage(self, state: EDMState) -> float:
        """Get target voltage with default."""
        return state.target_voltage or 80.0

    def _get_peak_current(self, state: EDMState) -> float:
        """Get peak current for current mode."""
        return self._get_current_from_mode(state.current_mode)

    def _get_on_time(self, state: EDMState) -> float:
        """Get ON time with default."""
        return state.ON_time or 3

    def _get_off_time(self, state: EDMState) -> float:
        """Get OFF time with default."""
        return state.OFF_time or 80

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    def get_lambda(self, state: EDMState) -> float:
        """Calculate ignition probability based on gap."""
        if state.is_short_circuit:
            raise ValueError("get_lambda called during short circuit condition.")

        gap = state.workpiece_position - state.wire_position

        if gap not in self.lambda_cache:
            self.lambda_cache[gap] = np.log(2) / (0.48 * gap**2 - 3.69 * gap + 14.05)

        return self.lambda_cache[gap]
