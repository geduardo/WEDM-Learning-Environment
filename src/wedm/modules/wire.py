# src/edm_env/modules/wire.py
from __future__ import annotations

import numpy as np

from ..core.module import EDMModule
from ..core.state import EDMState


class WireModule(EDMModule):
    """Optimized 1-D transient heat model of the travelling wire."""

    def __init__(
        self,
        env,
        buffer_len_bottom: float = 30.0,
        buffer_len_top: float = 30.0,
        spool_T: float = 293.15,
        segment_len: float = 0.2,
        compute_zone_mean: bool = False,  # Enable zone mean calculation if needed
    ):
        super().__init__(env)

        self.buffer_bottom = buffer_len_bottom
        self.buffer_top = buffer_len_top
        self.spool_T = spool_T
        self.seg_L = segment_len
        self.compute_zone_mean = compute_zone_mean  # Store the setting

        self.total_L = self.buffer_bottom + env.workpiece_height + self.buffer_top
        self.n_segments = max(1, int(self.total_L / self.seg_L))

        self.zone_start = int(self.buffer_bottom // self.seg_L)
        self.zone_end = self.zone_start + int(env.workpiece_height // self.seg_L)
        self.zone_end = min(self.zone_end, self.n_segments)
        self.zone_start = min(self.zone_start, self.zone_end)

        self.r_wire = env.wire_diameter / 2.0  # [mm]

        # Initialize wire temperature field
        if (
            not hasattr(env.state, "wire_temperature")
            or not isinstance(env.state.wire_temperature, np.ndarray)
            or len(env.state.wire_temperature) != self.n_segments
        ):
            env.state.wire_temperature = np.full(
                self.n_segments, self.spool_T, dtype=np.float32
            )

        # Material properties
        self.rho = 8400  # kg m⁻³
        self.cp = 377  # J kg⁻¹ K⁻¹
        self.k = 120  # W m⁻¹ K⁻¹
        self.rho_elec = 6.4e-8
        self.alpha_rho = 0.0039
        self.h_conv = 14_000
        self.eta_plasma = 0.1

        # Pre-compute constants for performance
        self.delta_y = self.seg_L * 1e-3  # [m]
        self.S = np.pi * (self.r_wire * 1e-3) ** 2
        self.A = 2 * np.pi * (self.r_wire * 1e-3) * self.delta_y
        self.k_cond_coeff = self.k * self.S / self.delta_y
        self.denominator = self.rho * self.cp * self.S * self.delta_y
        self.dt_sim = 1e-6
        self.temp_ref = 293.15
        self.joule_geom_factor = self.delta_y / self.S if self.S != 0 else 0.0

        # Pre-compute combined scaling factor
        self.temp_update_factor = self.dt_sim / self.denominator

        if self.denominator == 0:
            raise ValueError(
                "Denominator for dT/dt is zero. Check wire/segment properties."
            )

        # Pre-allocate arrays for performance
        self.dT_dt = np.zeros(self.n_segments, dtype=np.float32)
        self.T_rolled_plus1 = np.empty(self.n_segments, dtype=np.float32)
        self.T_rolled_minus1 = np.empty(self.n_segments, dtype=np.float32)
        self.q_cond_arr = np.empty(self.n_segments, dtype=np.float32)
        self.rho_T_arr = np.empty(self.n_segments, dtype=np.float32)
        self.q_joule_arr = np.empty(self.n_segments, dtype=np.float32)
        self.q_plasma_arr = np.zeros(self.n_segments, dtype=np.float32)
        self.T_minus_Tdielectric = np.empty(self.n_segments, dtype=np.float32)
        self.q_conv_arr = np.empty(self.n_segments, dtype=np.float32)
        self.q_adv_arr = np.empty(self.n_segments, dtype=np.float32)
        self.Trolled_m1_minus_T = np.empty(self.n_segments, dtype=np.float32)

        # Zone boundaries (for post-processing if needed)
        self.actual_zone_start = min(self.zone_start, self.n_segments - 1)
        self.actual_zone_end = min(self.zone_end, self.n_segments)

        if self.actual_zone_end > self.actual_zone_start:
            self.zone_size = self.actual_zone_end - self.actual_zone_start
        else:
            self.zone_size = 1

    def update(self, state: EDMState) -> None:
        if state.is_wire_broken:
            return

        # Fast path: avoid array length checks
        T = state.wire_temperature
        if len(T) != self.n_segments:
            state.wire_temperature = np.full(
                self.n_segments, self.spool_T, dtype=np.float32
            )
            T = state.wire_temperature

        # Initialize dT/dt
        self.dT_dt.fill(0.0)

        # Cache lookups for efficiency
        I = state.current or 0.0
        I_squared = I * I
        dielectric_temp = state.dielectric_temperature
        wire_unwind_vel = state.wire_unwinding_velocity

        # Apply boundary condition
        if self.n_segments >= 1:
            T[0] = self.spool_T

        # 1) Heat conduction
        if self.n_segments > 1:
            # Optimized array setup (avoid np.roll overhead)
            self.T_rolled_plus1[0] = T[-1]
            self.T_rolled_plus1[1:] = T[:-1]
            self.T_rolled_minus1[:-1] = T[1:]
            self.T_rolled_minus1[-1] = T[0]
        else:
            self.T_rolled_plus1[0] = T[0]
            self.T_rolled_minus1[0] = T[0]

        # Fused conduction calculation
        np.add(self.T_rolled_plus1, self.T_rolled_minus1, out=self.q_cond_arr)
        np.subtract(self.q_cond_arr, T, out=self.q_cond_arr)
        np.subtract(self.q_cond_arr, T, out=self.q_cond_arr)
        np.multiply(self.q_cond_arr, self.k_cond_coeff, out=self.q_cond_arr)

        # Apply Neumann boundary condition
        if self.n_segments > 1:
            idx_last = self.n_segments - 1
            self.q_cond_arr[idx_last] = self.k_cond_coeff * (
                T[idx_last - 1] - T[idx_last]
            )

        np.add(self.dT_dt, self.q_cond_arr, out=self.dT_dt)

        # 2) Joule heating
        if I_squared > 1e-6:  # Skip only for truly zero current
            np.subtract(T, self.temp_ref, out=self.rho_T_arr)
            np.multiply(self.rho_T_arr, self.alpha_rho, out=self.rho_T_arr)
            np.add(self.rho_T_arr, 1.0, out=self.rho_T_arr)
            np.multiply(self.rho_T_arr, self.rho_elec, out=self.rho_T_arr)

            joule_coeff = self.joule_geom_factor * I_squared
            np.multiply(self.rho_T_arr, joule_coeff, out=self.q_joule_arr)
            np.add(self.dT_dt, self.q_joule_arr, out=self.dT_dt)

        # 3) Plasma heating
        self.q_plasma_arr.fill(0.0)
        if state.spark_status[0] == 1 and state.spark_status[1] is not None:
            y_spark = state.spark_status[1]
            idx = (
                self.zone_start + int(y_spark // self.seg_L)
                if self.seg_L != 0
                else self.zone_start
            )
            if 0 <= idx < self.n_segments:
                voltage = state.voltage if state.voltage is not None else 0.0
                q_plasma_val = self.eta_plasma * voltage * I
                if np.isfinite(q_plasma_val):
                    self.q_plasma_arr[idx] = q_plasma_val
        np.add(self.dT_dt, self.q_plasma_arr, out=self.dT_dt)

        # 4) Convection
        h_eff = self.h_conv * (1.0 + 0.5 * wire_unwind_vel)

        # Get flow condition from dielectric module (dimensionless 0-1)
        flow_condition = state.flow_rate  # This is now the dimensionless flow condition

        # Calculate two convection coefficients: baseline and flow-enhanced
        baseline_conv_coeff = h_eff * self.A
        # Flow enhances convection: h_flow = h_base * (1 + flow_condition)
        # When flow_condition = 1 (max flow), convection doubles
        # When flow_condition = 0 (no flow), convection is baseline
        flow_enhanced_conv_coeff = baseline_conv_coeff * (1.0 + flow_condition)

        # Apply convection with zone-specific coefficients
        np.subtract(T, dielectric_temp, out=self.T_minus_Tdielectric)

        # Buffer zones use baseline convection
        if self.actual_zone_start > 0:
            s1 = slice(None, self.actual_zone_start)
            np.multiply(
                self.T_minus_Tdielectric[s1],
                baseline_conv_coeff,
                out=self.q_conv_arr[s1],
            )

        # Workpiece zone uses flow-enhanced convection
        if self.actual_zone_start < self.actual_zone_end:
            s2 = slice(self.actual_zone_start, self.actual_zone_end)
            np.multiply(
                self.T_minus_Tdielectric[s2],
                flow_enhanced_conv_coeff,
                out=self.q_conv_arr[s2],
            )

        # Top buffer zone uses baseline convection
        if self.actual_zone_end < self.n_segments:
            s3 = slice(self.actual_zone_end, None)
            np.multiply(
                self.T_minus_Tdielectric[s3],
                baseline_conv_coeff,
                out=self.q_conv_arr[s3],
            )

        np.subtract(self.dT_dt, self.q_conv_arr, out=self.dT_dt)

        # 5) Advection
        if abs(wire_unwind_vel) > 1e-6:  # Skip only for truly zero velocity
            v_wire = wire_unwind_vel * 1e-3  # m s⁻¹
            adv_coeff = self.rho * self.cp * v_wire * self.S / self.delta_y
            np.subtract(self.T_rolled_minus1, T, out=self.Trolled_m1_minus_T)
            np.multiply(self.Trolled_m1_minus_T, adv_coeff, out=self.q_adv_arr)
            np.add(self.dT_dt, self.q_adv_arr, out=self.dT_dt)

        # 6) Temperature update
        np.multiply(self.dT_dt, self.temp_update_factor, out=self.dT_dt)
        np.add(T, self.dT_dt, out=T)

        # Re-apply boundary condition
        if self.n_segments >= 1:
            T[0] = self.spool_T

        # Compute zone mean if requested (for logging/monitoring)
        if self.compute_zone_mean:
            state.wire_average_temperature = self.compute_zone_mean_temperature(T)
        # Note: When compute_zone_mean=False, wire_average_temperature can be computed
        # post-processing from the full temperature field if needed

    def compute_zone_mean_temperature(self, temperature_field: np.ndarray) -> float:
        """
        Compute zone mean temperature from full temperature field.

        This is more efficient than computing every microsecond when you only
        need it occasionally (e.g., for logging or post-processing).

        Args:
            temperature_field: Full wire temperature array

        Returns:
            Average temperature in the work zone [K]
        """
        if len(temperature_field) == 0:
            return self.spool_T
        elif self.zone_size > 0 and self.actual_zone_end <= len(temperature_field):
            # Optimized zone mean using slice and sum
            zone_sum = temperature_field[
                self.actual_zone_start : self.actual_zone_end
            ].sum()
            return float(zone_sum / self.zone_size)
        elif self.actual_zone_start < len(temperature_field):
            return float(temperature_field[self.actual_zone_start])
        else:
            return float(temperature_field.mean())
