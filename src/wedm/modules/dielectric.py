# src/wedm/modules/dielectric_optimized.py
from __future__ import annotations

import numpy as np
from numba import njit

from ..core.module import EDMModule
from ..core.state import EDMState


@njit(cache=True, fastmath=True)
def fast_exp(x):
    """Fast approximation of exp(-x) for x >= 0."""
    # Use Padé approximation for small x
    if x < 0.5:
        return (1 - 0.5 * x) / (1 + 0.5 * x)
    # Use standard exp for larger values
    return np.exp(-x)


class DielectricModule(EDMModule):
    """Optimized debris tracking and short circuit model for Wire EDM."""

    def __init__(
        self,
        env,
        base_flow_rate: float = 100.0,  # [mm³/s] Base pump/nozzle capacity
        debris_removal_efficiency: float = 0.01,  # β: Debris removal efficiency
        debris_obstruction_coeff: float = 1,  # k_debris: How much debris blocks flow
        reference_gap: float = 25.0,  # [μm] Reference gap for flow calculations
    ):
        super().__init__(env)

        # Physical parameters
        self.temp_K = 293.15
        self.wire_radius = env.wire_diameter / 2.0  # [mm]
        self.workpiece_height = env.workpiece_height  # [mm]

        # Debris tracking parameters
        self.f0 = base_flow_rate  # [mm³/s]
        self.beta = debris_removal_efficiency  # [dimensionless]
        self.k_debris = debris_obstruction_coeff  # [dimensionless]
        self.g_ref = reference_gap  # [μm]

        # Pre-compute constants
        self.cavity_volume_coeff = np.pi * self.wire_radius * self.workpiece_height
        self.g_ref_cubed = self.g_ref**3
        self.debris_removal_per_us = (
            self.beta * self.f0 * 1e-6
        )  # Pre-compute for μs timestep

        # Internal state
        self.debris_volume = 0.0  # [mm³]
        self.cavity_volume = 0.0  # [mm³]
        self.debris_density = 0.0  # [dimensionless]
        self.flow_condition = 0.0  # [dimensionless, 0-1]

        # Legacy compatibility
        self.ion_channel = None  # (y, remaining μs)
        self.tau_deion = 6  # μs

        # Cache for flow condition calculation
        self._last_gap_um = -1.0
        self._last_debris_density = -1.0
        self._last_flow_condition = 0.0

    def update(self, state: EDMState) -> None:
        """Optimized update with caching and reduced calculations."""
        # Update basic properties
        state.dielectric_temperature = self.temp_K

        # Calculate current gap with minimum value for numerical stability
        gap_um = max(0.001, state.workpiece_position - state.wire_position)  # [μm]

        # Fast cavity volume calculation (gap already in mm for this calc)
        gap_mm = gap_um * 0.001  # Convert to mm
        self.cavity_volume = self.cavity_volume_coeff * gap_mm

        # Add debris from fresh spark events (only real sparks, not short circuits)
        if state.spark_status[0] == 1 and state.spark_status[2] == 0:
            # Use crater volume from material module if available
            crater_volume = state.last_crater_volume
            if crater_volume > 0:
                self.debris_volume += crater_volume
                # Set up ionized channel for legacy compatibility
                self.ion_channel = (state.spark_status[1], self.tau_deion)

        # Update debris density
        if self.cavity_volume > 0:
            self.debris_density = min(1.0, self.debris_volume / self.cavity_volume)
        else:
            self.debris_density = 0.0

        # Calculate flow condition with caching
        if (
            abs(gap_um - self._last_gap_um) > 0.01
            or abs(self.debris_density - self._last_debris_density) > 0.001
        ):

            # Gap-dependent factor (Poiseuille-like flow)
            gap_factor = min(1.0, (gap_um / self.g_ref) ** 3)

            # Debris obstruction factor using fast exponential
            if self.k_debris * self.debris_density < 2.0:
                debris_factor = fast_exp(self.k_debris * self.debris_density)
            else:
                debris_factor = np.exp(-self.k_debris * self.debris_density)

            self.flow_condition = gap_factor * debris_factor

            # Update cache
            self._last_gap_um = gap_um
            self._last_debris_density = self.debris_density
            self._last_flow_condition = self.flow_condition
        else:
            # Use cached value
            self.flow_condition = self._last_flow_condition

        # Remove debris via flow (optimized with pre-computed rate)
        if self.flow_condition > 0.001 and self.debris_volume > 0.001:
            # Debris removed = β * f * dt, where f = flow_condition * f0
            debris_removed = self.debris_removal_per_us * self.flow_condition
            self.debris_volume = max(0.0, self.debris_volume - debris_removed)

        # Update ionized channel (legacy compatibility)
        if self.ion_channel:
            y_loc, t_left = self.ion_channel
            self.ion_channel = (y_loc, t_left - 1) if t_left > 1 else None

        # Sync to global state
        state.debris_volume = self.debris_volume
        state.debris_density = self.debris_density
        state.cavity_volume = self.cavity_volume
        state.flow_rate = self.flow_condition

        # Legacy compatibility
        state.debris_concentration = self.debris_density
        state.dielectric_flow_rate = (self.flow_condition * self.f0) / 1e9
        state.ionized_channel = self.ion_channel

    def reset_debris(self) -> None:
        """Reset debris tracking (useful for new simulations)."""
        self.debris_volume = 0.0
        self.debris_density = 0.0
        self.cavity_volume = 0.0
        self.flow_condition = 0.0
        self._last_gap_um = -1.0
        self._last_debris_density = -1.0

    def get_debris_statistics(self) -> dict:
        """Get current debris tracking statistics."""
        return {
            "debris_volume_mm3": self.debris_volume,
            "debris_density": self.debris_density,
            "cavity_volume_mm3": self.cavity_volume,
            "flow_condition": self.flow_condition,
            "debris_fill_percentage": self.debris_density * 100.0,
        }
