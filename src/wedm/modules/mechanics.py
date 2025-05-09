# src/edm_env/modules/mechanics.py
from __future__ import annotations

import numpy as np

from ..core.module import EDMModule
from ..core.state import EDMState


class MechanicsModule(EDMModule):
    """2nd-order servo axis with accel/jerk saturation."""

    omega_n = 100.0      # rad s⁻¹
    zeta = 0.75
    max_accel = 0.1 * 9.81 * 1e6        # [µm s⁻²]
    max_jerk = 300 * max_accel          # [µm s⁻³]
    max_speed = 3e6                     # [µm s⁻¹]

    def __init__(self, env):
        super().__init__(env)
        self.prev_accel = 0.0

    # ------------------------------------------------------------------ #
    def update(self, state: EDMState) -> None:
        dt = self.env.dt * 1e-6

        x = state.wire_position
        v = state.wire_velocity
        x_tgt = x + state.target_delta

        a_nom = -2 * self.zeta * self.omega_n * v - self.omega_n**2 * (x - x_tgt)
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
