# src/edm_env/modules/material.py
from __future__ import annotations

import json
import os
import numpy as np
from pathlib import Path

from ..core.module import EDMModule
from ..core.state import EDMState


class MaterialRemovalModule(EDMModule):
    """Material removal module using empirical crater volume distributions."""

    def __init__(self, env):
        super().__init__(env)
        # Load crater volume data from JSON file
        self.crater_data = self._load_crater_data()
        # Load machine current modes data
        self.currents_data = self._load_currents_data()

        # Cache for efficiency - avoid repeated current mode lookups
        self._cached_current_mode: str | None = None
        self._cached_machine_current: float = 60.0  # Default to I5
        self._cached_mapped_current: int = 1  # Default mapping
        self._cached_crater_info: dict = self.crater_data["1"]  # Default crater data

    def _load_crater_data(self) -> dict:
        """Load crater volume distributions from area_corrected.json."""
        # Get the path relative to this module
        current_dir = Path(__file__).parent
        json_path = current_dir / "area_corrected.json"

        try:
            with open(json_path, "r") as f:
                data = json.load(f)
            return data
        except FileNotFoundError:
            raise FileNotFoundError(f"Could not find crater data file at {json_path}")

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

    def update(self, state: EDMState) -> None:
        """Update material removal based on spark events and crater volumes."""
        # Only remove material during fresh sparks (transition from no spark to spark)
        if state.spark_status[0] == 1 and state.spark_status[2] == 0:
            # Fresh spark just ignited, calculate material removal
            crater_volume = self._sample_crater_volume(state)
            if crater_volume > 0:
                # Calculate workpiece position increment
                delta_x = self._calculate_position_increment(crater_volume, state)
                state.workpiece_position += delta_x

    def _sample_crater_volume(self, state: EDMState) -> float:
        """Sample crater volume from empirical distribution based on current mode."""
        current_mode = state.current_mode

        # Only recalculate if current_mode has changed
        if current_mode != self._cached_current_mode:
            if current_mode is None:
                current_mode = "I1"  # Default to I1 if not specified

            # Get actual current from current mode (0-18 maps to I1-I19)
            current_mode_key = current_mode
            if current_mode_key not in self.currents_data:
                # Fallback to I1 if invalid mode
                current_mode_key = "I1"

            self._cached_machine_current = self.currents_data[current_mode_key][
                "Current"
            ]  # In Amperes

            # Map machine current to available crater data current
            self._cached_mapped_current = self._map_machine_current_to_crater_data(
                self._cached_machine_current
            )

            # Get distribution parameters
            self._cached_crater_info = self.crater_data[
                str(self._cached_mapped_current)
            ]
            self._cached_current_mode = current_mode

        # Use cached crater info
        mean_volume = self._cached_crater_info[
            "ellipsoid_volume_half"
        ]  # Using half volume as it's more realistic
        std_volume = self._cached_crater_info["ellipsoid_volume_std"]

        # Sample from Gaussian distribution
        # Convert from micrometers³ to mm³ (divide by 1e9)
        sampled_volume_um3 = self.env.np_random.normal(mean_volume, std_volume)

        # Ensure non-negative volume
        sampled_volume_um3 = max(0, sampled_volume_um3)

        # Convert to mm³
        sampled_volume_mm3 = sampled_volume_um3 / 1e9

        return sampled_volume_mm3

    def _map_machine_current_to_crater_data(self, machine_current: float) -> int:
        """Map machine current (30-600A) to available crater data current (1-17A).

        Uses a scaling approach where machine currents are mapped to crater data currents
        based on relative position in their respective ranges.
        """
        # Machine current range: 30A (I1) to 600A (I19)
        machine_min, machine_max = 30, 600

        # Available crater data range: 1A to 17A
        crater_currents = [1, 3, 5, 7, 9, 11, 13, 15, 17]

        # Clamp machine current to valid range
        machine_current = max(machine_min, min(machine_max, machine_current))

        # Calculate relative position (0-1) in machine current range
        relative_pos = (machine_current - machine_min) / (machine_max - machine_min)

        # Map to crater data current index
        crater_index = int(relative_pos * (len(crater_currents) - 1))
        crater_index = max(0, min(len(crater_currents) - 1, crater_index))

        return crater_currents[crater_index]

    def _calculate_position_increment(
        self, crater_volume: float, state: EDMState
    ) -> float:
        """Calculate workpiece position increment from crater volume.

        Args:
            crater_volume: Crater volume in mm³
            state: Current EDM state

        Returns:
            Position increment in μm (same units as state positions)
        """
        # Calculate kerf width: k = base_overcut + wire_diameter + crater_depth
        base_overcut_mm = 0.12  # mm - base overcut (0.06mm per side)
        wire_diameter_mm = self.env.wire_diameter  # mm

        # Get crater depth from cached crater info (convert from μm to mm)
        crater_depth_um = self._cached_crater_info["depth"]  # μm
        crater_depth_mm = crater_depth_um / 1000.0  # Convert μm to mm

        kerf_width_mm = base_overcut_mm + wire_diameter_mm + crater_depth_mm  # mm

        # Workpiece height
        workpiece_height_mm = self.env.workpiece_height  # mm

        # Calculate position increment: ΔXw = Vc / (k * hw)
        # Result will be in mm, then convert to μm
        if kerf_width_mm > 0 and workpiece_height_mm > 0:
            delta_x_mm = crater_volume / (kerf_width_mm * workpiece_height_mm)  # mm
            delta_x_um = delta_x_mm * 1000.0  # Convert mm to μm to match state units
        else:
            delta_x_um = 0.0

        return delta_x_um

    def get_crater_data_for_current_mode(self, current_mode: str) -> dict:
        """Get crater data for a specific current mode (for debugging/analysis)."""
        current_mode_key = current_mode
        if current_mode_key not in self.currents_data:
            current_mode_key = "I1"

        machine_current = self.currents_data[current_mode_key]["Current"]
        mapped_current = self._map_machine_current_to_crater_data(machine_current)

        return {
            "current_mode": current_mode_key,
            "machine_current": machine_current,
            "mapped_crater_current": mapped_current,
            "crater_data": self.crater_data[str(mapped_current)],
        }

    def get_current_mapping_table(self) -> dict:
        """Get complete mapping table from current modes to crater data (for debugging)."""
        mapping = {}
        for i in range(19):  # I1 to I19 (0-18)
            mapping[f"I{i+1}"] = self.get_crater_data_for_current_mode(f"I{i+1}")
        return mapping
