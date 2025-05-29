# src/edm_env/modules/dielectric.py
from __future__ import annotations

import numpy as np

from ..core.module import EDMModule
from ..core.state import EDMState


class DielectricModule(EDMModule):
    """Advanced debris tracking and short circuit model for Wire EDM."""

    def __init__(
        self,
        env,
        base_flow_rate: float = 100.0,  # [mm³/s] Base pump/nozzle capacity
        debris_removal_efficiency: float = 0.001,  # β: Debris removal efficiency
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

        # Internal state
        self.debris_volume = 0.0  # [mm³]
        self.cavity_volume = 0.0  # [mm³]
        self.debris_density = 0.0  # [dimensionless]
        self.flow_condition = (
            0.0  # [dimensionless, 0-1] where 1 = maximum possible flow
        )

        # Legacy compatibility
        self.ion_channel = None  # (y, remaining μs)
        self.tau_deion = 6  # μs

    def update(self, state: EDMState) -> None:
        """Update debris tracking and dielectric properties."""
        # Update basic properties
        state.dielectric_temperature = self.temp_K

        # Calculate current gap (convert from μm to mm for internal calculations)
        gap_um = max(0.001, state.workpiece_position - state.wire_position)  # [μm]
        gap_mm = gap_um / 1000.0  # [mm]

        # Calculate cavity volume
        self.cavity_volume = self._calculate_cavity_volume(gap_mm)

        # Add debris from fresh spark events (only real sparks, not short circuits)
        if state.spark_status[0] == 1 and state.spark_status[2] == 0:
            # Use crater volume from material module if available (only for real sparks)
            crater_volume = state.last_crater_volume
            if crater_volume > 0:
                self.debris_volume += crater_volume
                # Set up ionized channel for legacy compatibility
                self.ion_channel = (state.spark_status[1], self.tau_deion)

        # Calculate current flow condition
        self.flow_condition = self._calculate_flow_condition(
            gap_um, self.debris_density
        )

        # Remove debris via flow
        if self.flow_condition > 0 and self.debris_volume > 0:
            # Calculate debris removed in one timestep (1 μs)
            # Use actual flow rate for debris removal: flow_condition * max_flow_rate
            actual_flow_rate = self.flow_condition * self.f0  # [mm³/s]
            dt_s = 1e-6  # 1 μs timestep in seconds
            debris_removed = self.beta * actual_flow_rate * dt_s  # [mm³]
            self.debris_volume = max(0.0, self.debris_volume - debris_removed)

        # Update debris density
        if self.cavity_volume > 0:
            self.debris_density = min(1.0, self.debris_volume / self.cavity_volume)
        else:
            self.debris_density = 0.0

        # Update ionized channel (legacy compatibility)
        if self.ion_channel:
            y_loc, t_left = self.ion_channel
            self.ion_channel = (y_loc, t_left - 1) if t_left > 1 else None

        # Sync to global state
        state.debris_volume = self.debris_volume
        state.debris_density = self.debris_density
        state.cavity_volume = self.cavity_volume
        state.flow_rate = (
            self.flow_condition
        )  # Now stores dimensionless flow condition (0-1)

        # Legacy compatibility
        state.debris_concentration = self.debris_density  # Map to legacy field
        state.dielectric_flow_rate = (
            self.flow_condition * self.f0
        ) / 1e9  # Convert to m³/s for legacy
        state.ionized_channel = self.ion_channel

    def _calculate_cavity_volume(self, gap_mm: float) -> float:
        """
        Calculate cavity volume as frontal half-cylinder.

        V = π * r * h * g

        Args:
            gap_mm: Gap between wire and workpiece [mm]

        Returns:
            Cavity volume [mm³]
        """
        return np.pi * self.wire_radius * self.workpiece_height * gap_mm

    def _calculate_flow_condition(self, gap_um: float, debris_density: float) -> float:
        """
        Calculate dielectric flow condition with gap and debris effects.

        f_condition = f_gap(g) * f_debris(ρ)

        Args:
            gap_um: Gap between wire and workpiece [μm]
            debris_density: Current debris density [dimensionless]

        Returns:
            Flow condition [dimensionless, 0-1] where 1 = maximum possible flow
        """
        # Gap-dependent factor (Poiseuille-like flow)
        f_gap = min(1.0, (gap_um / self.g_ref) ** 3)

        # Debris obstruction factor (exponential decay)
        f_debris = np.exp(-self.k_debris * debris_density)

        # Return normalized flow condition (0-1)
        return f_gap * f_debris

    def reset_debris(self) -> None:
        """Reset debris tracking (useful for new simulations)."""
        self.debris_volume = 0.0
        self.debris_density = 0.0
        self.cavity_volume = 0.0
        self.flow_condition = 0.0

    def get_debris_statistics(self) -> dict:
        """Get current debris tracking statistics."""
        return {
            "debris_volume_mm3": self.debris_volume,
            "debris_density": self.debris_density,
            "cavity_volume_mm3": self.cavity_volume,
            "flow_condition": self.flow_condition,
            "debris_fill_percentage": self.debris_density * 100.0,
        }
