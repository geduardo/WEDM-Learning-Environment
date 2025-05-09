# src/edm_env/modules/wire.py
from __future__ import annotations

import numpy as np

from ..core.module import EDMModule
from ..core.state import EDMState


class WireModule(EDMModule):
    """1-D transient heat model of the travelling wire."""

    def __init__(
        self,
        env,
        buffer_len_bottom: float = 50.0,
        buffer_len_top: float = 20.0,
        spool_T: float = 293.15,
        segment_len: float = 0.2,
    ):
        super().__init__(env)

        self.buffer_bottom = buffer_len_bottom
        self.buffer_top = buffer_len_top
        self.spool_T = spool_T
        self.seg_L = segment_len

        self.total_L = self.buffer_bottom + env.workpiece_height + self.buffer_top
        self.n_segments = int(self.total_L / self.seg_L)

        self.zone_start = int(self.buffer_bottom // self.seg_L)
        self.zone_end = self.zone_start + int(env.workpiece_height // self.seg_L)

        self.r_wire = env.wire_diameter / 2.0  # [mm]

        # wire temperature field
        if state_arr := env.state.wire_temperature:
            if len(state_arr) != self.n_segments:
                env.state.wire_temperature = np.full(
                    self.n_segments, self.spool_T, dtype=np.float32
                )
        else:
            env.state.wire_temperature = np.full(
                self.n_segments, self.spool_T, dtype=np.float32
            )

        # Material props (brass default)
        self.rho = 8400  # kg m⁻³
        self.cp = 377  # J kg⁻¹ K⁻¹
        self.k = 120  # W m⁻¹ K⁻¹
        self.rho_elec = 6.4e-8
        self.alpha_rho = 0.0039

        self.h_conv = 14_000
        self.eta_plasma = 0.1

        self.delta_y = self.seg_L * 1e-3  # [m]
        self.S = np.pi * (self.r_wire * 1e-3) ** 2
        self.A = 2 * np.pi * (self.r_wire * 1e-3) * self.delta_y
        self.k_cond = self.k * self.S / self.delta_y
        self.denominator = self.rho * self.cp * self.S * self.delta_y

    # ------------------------------------------------------------------ #
    def update(self, state: EDMState) -> None:
        if state.is_wire_broken:
            return

        # Initialize wire temperature array if it's empty
        if len(state.wire_temperature) == 0:
            state.wire_temperature = np.full(
                self.n_segments, self.spool_T, dtype=np.float32
            )

        # Initialize spark_status if it's not properly set
        if not state.spark_status or len(state.spark_status) < 3:
            state.spark_status = [0, None, 0]

        T = state.wire_temperature
        I = state.current or 0.0
        dt = 1e-6  # 1 µs

        # 1) Dirichlet boundaries
        T[0] = T[-1] = self.spool_T

        # 2) Conduction
        q_cond = self.k_cond * (np.roll(T, 1) - 2 * T + np.roll(T, -1))

        # 3) Joule
        rho_T = self.rho_elec * (1 + self.alpha_rho * (T - 293.15))
        q_joule = 0.5 * (I**2) * rho_T * (self.delta_y / self.S)

        # 4) Plasma spot heating
        q_plasma = np.zeros_like(T)
        if state.spark_status[0] == 1 and state.spark_status[1] is not None:
            y = state.spark_status[1]
            idx = self.zone_start + int(y // self.seg_L)
            idx = np.clip(idx, 0, self.n_segments - 1)
            q_plasma[idx] = self.eta_plasma * state.voltage * I

        # 5) Convection
        h_eff = self.h_conv * (1 + 0.5 * state.wire_unwinding_velocity)
        q_conv = h_eff * self.A * (T - state.dielectric_temperature)

        # 6) Advection
        v = state.wire_unwinding_velocity * 1e-3  # m s⁻¹
        q_adv = self.rho * self.cp * v * self.S / self.delta_y * (np.roll(T, -1) - T)

        # 7) Update
        dT_dt = (q_plasma + q_joule + q_cond - q_conv + q_adv) / self.denominator
        T += dT_dt * dt
        T[0] = T[-1] = self.spool_T

        # Mean temp in work zone
        zone = T[self.zone_start : self.zone_end]
        state.wire_average_temperature = float(zone.mean() if zone.size else T.mean())
