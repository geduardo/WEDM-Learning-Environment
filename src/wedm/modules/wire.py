# src/wedm/modules/wire_optimized.py
from __future__ import annotations

import numpy as np
from numba import njit, prange

from ..core.module import EDMModule
from ..core.state import EDMState


# Numba-compiled functions for performance-critical calculations
@njit(cache=True, fastmath=True)
def compute_thermal_update(
    T,
    dT_dt,
    n_segments,
    spool_T,
    k_cond_coeff,
    I_squared,
    joule_geom_factor,
    rho_elec,
    alpha_rho,
    temp_ref,
    plasma_idx,
    plasma_heat,
    h_eff_base,
    h_eff_zone,
    dielectric_temp,
    A,
    adv_coeff,
    temp_update_factor,
):
    """Optimized thermal update computation using Numba."""
    # Apply boundary condition
    T[0] = spool_T

    # Reset dT/dt
    dT_dt[:] = 0.0

    # 1) Conduction - optimized with single pass
    if n_segments > 1:
        # Interior points
        for i in prange(1, n_segments - 1):
            dT_dt[i] = k_cond_coeff * (T[i - 1] - 2 * T[i] + T[i + 1])

        # Neumann BC at last segment
        dT_dt[n_segments - 1] = k_cond_coeff * (T[n_segments - 2] - T[n_segments - 1])

    # 2) Joule heating - fused operations
    if I_squared > 1e-6:
        joule_factor = joule_geom_factor * I_squared * rho_elec
        for i in prange(n_segments):
            rho_T = 1.0 + alpha_rho * (T[i] - temp_ref)
            dT_dt[i] += joule_factor * rho_T

    # 3) Plasma heating
    if plasma_idx >= 0 and plasma_idx < n_segments:
        dT_dt[plasma_idx] += plasma_heat

    # 4) Convection - optimized with precomputed coefficients
    for i in prange(n_segments):
        conv_coeff = h_eff_zone[i] * A
        dT_dt[i] -= conv_coeff * (T[i] - dielectric_temp)

    # 5) Advection
    if abs(adv_coeff) > 1e-9:
        for i in prange(1, n_segments):
            dT_dt[i] += adv_coeff * (T[i - 1] - T[i])

    # 6) Temperature update
    for i in prange(n_segments):
        T[i] += dT_dt[i] * temp_update_factor

    # Re-apply boundary condition
    T[0] = spool_T


class WireModule(EDMModule):
    """Optimized 1-D transient heat model of the travelling wire."""

    def __init__(
        self,
        env,
        buffer_len_bottom: float = 30.0,
        buffer_len_top: float = 30.0,
        spool_T: float = 293.15,
        segment_len: float = 0.2,
        compute_zone_mean: bool = False,
        zone_mean_interval: int = 100,  # Compute zone mean every N steps
    ):
        super().__init__(env)

        self.buffer_bottom = buffer_len_bottom
        self.buffer_top = buffer_len_top
        self.spool_T = spool_T
        self.seg_L = segment_len
        self.compute_zone_mean = compute_zone_mean
        self.zone_mean_interval = zone_mean_interval
        self.zone_mean_counter = 0

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

        # Pre-compute zone-specific heat transfer coefficients
        self.h_eff_zone = np.zeros(self.n_segments, dtype=np.float32)

        # Zone boundaries
        self.actual_zone_start = min(self.zone_start, self.n_segments - 1)
        self.actual_zone_end = min(self.zone_end, self.n_segments)

        if self.actual_zone_end > self.actual_zone_start:
            self.zone_size = self.actual_zone_end - self.actual_zone_start
        else:
            self.zone_size = 1

        # Cache for last computed zone mean
        self._last_zone_mean = self.spool_T
        self._last_flow_condition = 0.0

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

        # Cache lookups for efficiency
        I = state.current or 0.0
        I_squared = I * I
        dielectric_temp = state.dielectric_temperature
        wire_unwind_vel = state.wire_unwinding_velocity

        # Update convection coefficients only when flow condition changes significantly
        flow_condition = state.flow_rate
        if abs(flow_condition - self._last_flow_condition) > 0.01:
            self._update_convection_coefficients(wire_unwind_vel, flow_condition)
            self._last_flow_condition = flow_condition

        # Prepare plasma heating
        plasma_idx = -1
        plasma_heat = 0.0
        if state.spark_status[0] == 1 and state.spark_status[1] is not None:
            y_spark = state.spark_status[1]
            plasma_idx = (
                self.zone_start + int(y_spark // self.seg_L)
                if self.seg_L != 0
                else self.zone_start
            )
            if 0 <= plasma_idx < self.n_segments:
                voltage = state.voltage if state.voltage is not None else 0.0
                plasma_heat = self.eta_plasma * voltage * I
                if not np.isfinite(plasma_heat):
                    plasma_heat = 0.0

        # Advection coefficient
        if abs(wire_unwind_vel) > 1e-6:
            v_wire = wire_unwind_vel * 1e-3  # m s⁻¹
            adv_coeff = self.rho * self.cp * v_wire * self.S / self.delta_y
        else:
            adv_coeff = 0.0

        # Call optimized Numba function
        compute_thermal_update(
            T,
            self.dT_dt,
            self.n_segments,
            self.spool_T,
            self.k_cond_coeff,
            I_squared,
            self.joule_geom_factor,
            self.rho_elec,
            self.alpha_rho,
            self.temp_ref,
            plasma_idx,
            plasma_heat,
            self.h_conv,
            self.h_eff_zone,
            dielectric_temp,
            self.A,
            adv_coeff,
            self.temp_update_factor,
        )

        # Compute zone mean only when needed
        if self.compute_zone_mean:
            self.zone_mean_counter += 1
            if self.zone_mean_counter >= self.zone_mean_interval:
                self._last_zone_mean = self._compute_zone_mean_fast(T)
                state.wire_average_temperature = self._last_zone_mean
                self.zone_mean_counter = 0
            else:
                # Use cached value
                state.wire_average_temperature = self._last_zone_mean

    def _update_convection_coefficients(
        self, wire_unwind_vel: float, flow_condition: float
    ):
        """Update zone-specific convection coefficients."""
        h_eff_base = self.h_conv * (1.0 + 0.5 * wire_unwind_vel)
        h_eff_enhanced = h_eff_base * (1.0 + flow_condition)

        # Fill array with appropriate values
        self.h_eff_zone.fill(h_eff_base)
        if self.actual_zone_start < self.actual_zone_end:
            self.h_eff_zone[self.actual_zone_start : self.actual_zone_end] = (
                h_eff_enhanced
            )

    def _compute_zone_mean_fast(self, T: np.ndarray) -> float:
        """Fast zone mean computation."""
        if self.zone_size > 0 and self.actual_zone_end <= len(T):
            return float(np.mean(T[self.actual_zone_start : self.actual_zone_end]))
        return float(np.mean(T))

    def compute_zone_mean_temperature(self, temperature_field: np.ndarray) -> float:
        """Public method for on-demand zone mean calculation."""
        return self._compute_zone_mean_fast(temperature_field)
