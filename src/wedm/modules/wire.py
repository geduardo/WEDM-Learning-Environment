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
        self.n_segments = max(1, int(self.total_L / self.seg_L))

        self.zone_start = int(self.buffer_bottom // self.seg_L)
        self.zone_end = self.zone_start + int(env.workpiece_height // self.seg_L)
        self.zone_end = min(self.zone_end, self.n_segments)
        self.zone_start = min(self.zone_start, self.zone_end)

        self.r_wire = env.wire_diameter / 2.0  # [mm]

        # wire temperature field
        if (
            not hasattr(env.state, "wire_temperature")
            or not isinstance(env.state.wire_temperature, np.ndarray)
            or len(env.state.wire_temperature) != self.n_segments
        ):
            env.state.wire_temperature = np.full(
                self.n_segments, self.spool_T, dtype=np.float32
            )
        else:
            env.state.wire_temperature = np.asarray(
                env.state.wire_temperature, dtype=np.float32
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
        self.k_cond_coeff = self.k * self.S / self.delta_y
        self.denominator = self.rho * self.cp * self.S * self.delta_y
        if self.denominator == 0:
            raise ValueError(
                "Denominator for dT/dt is zero. Check wire/segment properties."
            )

        # Pre-allocate arrays for the update method
        self.T_rolled_plus1 = np.empty(self.n_segments, dtype=np.float32)
        self.T_rolled_minus1 = np.empty(self.n_segments, dtype=np.float32)

        self.rho_T_arr = np.empty(self.n_segments, dtype=np.float32)
        self.q_joule_arr = np.empty(self.n_segments, dtype=np.float32)
        self.q_plasma_arr = np.zeros(self.n_segments, dtype=np.float32)
        self.T_minus_Tdielectric = np.empty(self.n_segments, dtype=np.float32)
        self.q_conv_arr = np.empty(self.n_segments, dtype=np.float32)
        self.Trolled_m1_minus_T = np.empty(self.n_segments, dtype=np.float32)
        self.q_adv_arr = np.empty(self.n_segments, dtype=np.float32)
        self.dT_dt = np.empty(self.n_segments, dtype=np.float32)

    # ------------------------------------------------------------------ #
    def update(self, state: EDMState) -> None:
        if state.is_wire_broken:
            return

        # Safeguard initialization of wire_temperature if somehow missed or incorrect
        if len(state.wire_temperature) != self.n_segments:
            state.wire_temperature = np.full(
                self.n_segments, self.spool_T, dtype=np.float32
            )

        T = state.wire_temperature

        # Initialize spark_status if it's not properly set
        if not state.spark_status or len(state.spark_status) < 3:
            state.spark_status = [0, None, 0]

        I = state.current or 0.0
        dt_sim = 1e-6  # Simulation timestep, assumed 1 µs from original

        # Ensure boundary conditions are set on T before use for "rolled" arrays
        if self.n_segments == 1:
            T[0] = self.spool_T
        elif self.n_segments > 1:
            T[0] = self.spool_T
            T[-1] = self.spool_T

        # 1) Prepare "rolled" arrays using slicing (replaces np.roll)
        if self.n_segments == 1:
            self.T_rolled_plus1[0] = T[0]
            self.T_rolled_minus1[0] = T[0]
        elif self.n_segments > 1:
            self.T_rolled_plus1[0] = T[-1]
            self.T_rolled_plus1[1:] = T[:-1]

            self.T_rolled_minus1[-1] = T[0]
            self.T_rolled_minus1[:-1] = T[1:]

        # 2) Conduction: q_cond = self.k_cond_coeff * (T_rolled_plus1 - 2*T + T_rolled_minus1)
        np.subtract(self.T_rolled_plus1, T, out=self.dT_dt)
        np.subtract(self.dT_dt, T, out=self.dT_dt)
        np.add(self.dT_dt, self.T_rolled_minus1, out=self.dT_dt)
        np.multiply(self.dT_dt, self.k_cond_coeff, out=self.dT_dt)

        # 3) Joule heating: q_joule = 0.5 * (I**2) * rho_T * (self.delta_y / self.S)
        np.subtract(T, 293.15, out=self.rho_T_arr)
        np.multiply(self.rho_T_arr, self.alpha_rho, out=self.rho_T_arr)
        np.add(self.rho_T_arr, 1, out=self.rho_T_arr)
        np.multiply(self.rho_T_arr, self.rho_elec, out=self.rho_T_arr)
        joule_coeff = 0.5 * (I**2) * (self.delta_y / self.S)
        np.multiply(self.rho_T_arr, joule_coeff, out=self.q_joule_arr)
        np.add(self.dT_dt, self.q_joule_arr, out=self.dT_dt)

        # 4) Plasma spot heating: q_plasma[idx] = self.eta_plasma * state.voltage * I
        self.q_plasma_arr[:] = 0.0
        if state.spark_status[0] == 1 and state.spark_status[1] is not None:
            y_spark = state.spark_status[1]
            idx = self.zone_start + int(y_spark // self.seg_L)
            if 0 <= idx < self.n_segments:
                self.q_plasma_arr[idx] = self.eta_plasma * state.voltage * I
        np.add(self.dT_dt, self.q_plasma_arr, out=self.dT_dt)

        # 5) Convection: q_conv = h_eff * self.A * (T - state.dielectric_temperature)
        h_eff = self.h_conv * (1 + 0.5 * state.wire_unwinding_velocity)
        conv_coeff = h_eff * self.A
        np.subtract(T, state.dielectric_temperature, out=self.T_minus_Tdielectric)
        np.multiply(self.T_minus_Tdielectric, conv_coeff, out=self.q_conv_arr)
        np.subtract(self.dT_dt, self.q_conv_arr, out=self.dT_dt)

        # 6) Advection: q_adv = self.rho * self.cp * v * self.S / self.delta_y * (T_rolled_minus1 - T)
        v_wire = state.wire_unwinding_velocity * 1e-3  # m s⁻¹
        adv_coeff = self.rho * self.cp * v_wire * self.S / self.delta_y
        np.subtract(self.T_rolled_minus1, T, out=self.Trolled_m1_minus_T)
        np.multiply(self.Trolled_m1_minus_T, adv_coeff, out=self.q_adv_arr)
        np.add(self.dT_dt, self.q_adv_arr, out=self.dT_dt)

        # 7) Update Temperature: T += (dT_dt_total / denominator) * dt_sim
        np.divide(self.dT_dt, self.denominator, out=self.dT_dt)
        np.multiply(self.dT_dt, dt_sim, out=self.dT_dt)
        np.add(T, self.dT_dt, out=T)

        # Re-apply Dirichlet boundary conditions
        if self.n_segments == 1:
            T[0] = self.spool_T
        elif self.n_segments > 1:
            T[0] = self.spool_T
            T[-1] = self.spool_T

        # Mean temp in work zone
        if self.n_segments == 0:
            state.wire_average_temperature = self.spool_T
        else:
            actual_zone_start = min(self.zone_start, self.n_segments - 1)
            actual_zone_end = min(self.zone_end, self.n_segments)

            if actual_zone_end > actual_zone_start:
                zone = T[actual_zone_start:actual_zone_end]
                state.wire_average_temperature = float(zone.mean())
            else:
                state.wire_average_temperature = float(T.mean())
