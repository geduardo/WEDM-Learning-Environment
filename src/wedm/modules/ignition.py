# src/wedm/modules/ignition_optimized.py
from __future__ import annotations

import json
import numpy as np
from pathlib import Path

from ..core.module import EDMModule
from ..core.state import EDMState


class IgnitionModule(EDMModule):
    """Optimized stochastic plasma-channel ignition model."""

    def __init__(self, env):
        super().__init__(env)

        # Enhanced lambda caching with tolerance-based lookup
        self.lambda_cache: dict[int, float] = {}  # Use integer micrometers as keys
        self.gap_tolerance = 0.1  # Cache tolerance in micrometers

        # Pre-compute constants for lambda calculation
        self.ln2 = np.log(2)

        # Load machine current modes data
        self.currents_data = self._load_currents_data()

        # Cache for efficiency
        self._cached_current_mode: str | None = None
        self._cached_current_value: float = 60.0  # Default to I5 current

        # Pre-compute state transition times
        self._cached_on_time: float = 3.0
        self._cached_off_time: float = 80.0
        self._cached_total_time: float = 83.0

    def _load_currents_data(self) -> dict:
        """Load current mode mappings from currents.json."""
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
        if current_mode != self._cached_current_mode:
            if current_mode is None:
                current_mode = "I5"

            if current_mode not in self.currents_data:
                current_mode = "I5"

            self._cached_current_value = self.currents_data[current_mode]["Current"]
            self._cached_current_mode = current_mode

        return self._cached_current_value

    def update(self, state: EDMState) -> None:
        """Optimized update with reduced function calls and caching."""

        # Step 1: Fast short circuit detection
        gap = state.workpiece_position - state.wire_position
        state.is_short_circuit = gap < 2.0

        # Step 2: Force voltage to 0 if short circuit
        if state.is_short_circuit:
            state.voltage = 0

        # Step 3: Optimized state machine with cached values
        spark_state = state.spark_status[0]

        # Cache timing parameters if they changed
        if state.ON_time and state.ON_time != self._cached_on_time:
            self._cached_on_time = state.ON_time
            self._update_total_time()
        if state.OFF_time and state.OFF_time != self._cached_off_time:
            self._cached_off_time = state.OFF_time
            self._update_total_time()

        # Direct state dispatch without method calls
        if spark_state == 0:  # IDLE
            state.current = 0

            if state.is_short_circuit:
                # Short circuit during idle → deliver pulse
                state.spark_status = [-1, None, 0]
                state.current = self._get_current_from_mode(state.current_mode)
            else:
                # Normal idle → set voltage and check for ignition
                state.voltage = state.target_voltage or 80.0

                # Optimized ignition check
                if gap > 0 and self._should_ignite_fast(gap):
                    # Start normal spark
                    spark_location = self.env.np_random.uniform(
                        0, self.env.workpiece_height
                    )
                    state.spark_status = [1, spark_location, 0]
                    state.voltage = (state.target_voltage or 80.0) * 0.3
                    state.current = self._get_current_from_mode(state.current_mode)

        elif spark_state == 1:  # SPARK
            duration = state.spark_status[2] + 1
            state.spark_status[2] = duration

            if duration >= self._cached_on_time:
                # Spark finished → go to rest
                state.spark_status[0] = -2
                state.current = 0
                if not state.is_short_circuit:
                    state.voltage = 0
            else:
                # Continue spark
                state.current = self._get_current_from_mode(state.current_mode)
                if not state.is_short_circuit:
                    state.voltage = (state.target_voltage or 80.0) * 0.3

        elif spark_state == -1:  # SHORT
            duration = state.spark_status[2] + 1
            state.spark_status[2] = duration

            if duration >= self._cached_on_time:
                # Short pulse finished → go to rest
                state.spark_status[0] = -2
                state.current = 0
            else:
                # Continue short pulse
                state.current = self._get_current_from_mode(state.current_mode)

        elif spark_state == -2:  # REST
            duration = state.spark_status[2] + 1
            state.spark_status[2] = duration

            if duration >= self._cached_total_time:
                # Rest finished → back to idle
                state.spark_status = [0, None, 0]
                state.current = 0
                if not state.is_short_circuit:
                    state.voltage = state.target_voltage or 80.0
            else:
                # Continue rest
                state.current = 0
                if not state.is_short_circuit:
                    state.voltage = 0

    def _should_ignite_fast(self, gap: float) -> bool:
        """Optimized ignition check with improved caching."""
        # Convert to integer micrometers for cache key
        gap_key = int(gap * 10)  # 0.1 micrometer resolution

        if gap_key not in self.lambda_cache:
            # Calculate lambda using optimized formula
            gap_sq = gap * gap
            denominator = 0.48 * gap_sq - 3.69 * gap + 14.05
            self.lambda_cache[gap_key] = self.ln2 / denominator

        return self.env.np_random.random() < self.lambda_cache[gap_key]

    def _update_total_time(self):
        """Update cached total cycle time."""
        self._cached_total_time = self._cached_on_time + self._cached_off_time

    def get_lambda(self, state: EDMState) -> float:
        """Calculate ignition probability based on gap (for compatibility)."""
        if state.is_short_circuit:
            raise ValueError("get_lambda called during short circuit condition.")

        gap = state.workpiece_position - state.wire_position
        gap_key = int(gap * 10)

        if gap_key not in self.lambda_cache:
            gap_sq = gap * gap
            denominator = 0.48 * gap_sq - 3.69 * gap + 14.05
            self.lambda_cache[gap_key] = self.ln2 / denominator

        return self.lambda_cache[gap_key]
