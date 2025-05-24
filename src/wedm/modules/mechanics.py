# src/edm_env/modules/mechanics.py
from __future__ import annotations

import numpy as np

from ..core.module import EDMModule
from ..core.state import EDMState


class MechanicsModule(EDMModule):
    """Servo axis with configurable position or velocity control modes."""

    def __init__(self, env, control_mode: str = "position"):
        super().__init__(env)

        # Validate control mode
        if control_mode not in ["position", "velocity"]:
            raise ValueError(
                f"control_mode must be 'position' or 'velocity', got {control_mode}"
            )

        self.control_mode = control_mode

        # Parameters
        self.omega_n = 200  # rad s⁻¹
        self.zeta = 0.55  # damping ratio (only used for position control)
        self.max_accel = 3 * 1e5  # [µm s⁻²]
        self.max_jerk = 10 * 1e7  # [µm s⁻³]
        self.max_speed = 3e4  # [µm s⁻¹]

        self.prev_accel = 0.0

        # Method dispatch: set up control law computation during init to avoid conditionals in hot path
        if control_mode == "position":
            self._compute_nominal_accel = self._compute_position_accel
        else:  # velocity
            self._compute_nominal_accel = self._compute_velocity_accel

    # ------------------------------------------------------------------ #
    def _compute_position_accel(self, state: EDMState, x: float, v: float) -> float:
        """Position control: target_delta represents position increment [µm]."""
        x_tgt = x + state.target_delta
        return -2 * self.zeta * self.omega_n * v - self.omega_n**2 * (x - x_tgt)

    def _compute_velocity_accel(self, state: EDMState, x: float, v: float) -> float:
        """Velocity control: target_delta represents target velocity [µm/s]."""
        v_tgt = state.target_delta
        return -self.omega_n * (v - v_tgt)

    def update(self, state: EDMState) -> None:
        dt = self.env.dt * 1e-6

        x = state.wire_position
        v = state.wire_velocity

        # Compute nominal acceleration using dispatched method (no conditionals!)
        a_nom = self._compute_nominal_accel(state, x, v)

        # Common acceleration and jerk limiting
        a_nom = np.clip(a_nom, -self.max_accel, self.max_accel)

        da = a_nom - self.prev_accel
        da = np.clip(da, -self.max_jerk * dt, self.max_jerk * dt)

        a = self.prev_accel + da
        self.prev_accel = a

        v += a * dt
        v = np.clip(v, -self.max_speed, self.max_speed)

        x += v * dt

        state.wire_velocity = v
        state.wire_position = x
