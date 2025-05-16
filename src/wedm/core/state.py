# src/edm_env/core/state.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np

# ──────────────────────────────────────────────────────────────────────────────
# Low-level types
# ──────────────────────────────────────────────────────────────────────────────
crater_dtype = np.dtype(
    [
        ("radius", "f4"),  # crater radius       [µm]
        ("y_position", "f4"),  # axial position      [mm]
        ("time_formed", "i4"),  # timestamp           [µs]
        ("depth", "f4"),  # crater depth        [µm]
    ]
)


# ──────────────────────────────────────────────────────────────────────────────
# Global process state – every module reads & writes this
# ──────────────────────────────────────────────────────────────────────────────
@dataclass
class EDMState:
    # Time bookkeeping (µs)

    time: int = 0  # Current time from start of simulation
    time_since_servo: int = 0  # Time since last servo action
    time_since_open_voltage: int = 0  # Time since last voltage was applied
    time_since_spark_ignition: int = 0  # Time since last spark was ignited
    time_since_spark_end: int = 0  # Time since last spark ended

    # Electrical
    voltage: Optional[float] = None  # [V] Voltage between wire and workpiece
    current: Optional[float] = None  # [A] Current flowing through the circuit

    # Generator control state variables
    target_voltage: Optional[float] = None
    peak_current: Optional[float] = None
    OFF_time: Optional[float] = None
    ON_time: Optional[float] = None

    # Positions / motion
    workpiece_position: float = 0.0  # [µm]
    wire_position: float = 0.0  # [µm]
    wire_velocity: float = 0.0  # [µm s⁻¹]
    wire_unwinding_velocity: float = 0.1  # [µm µs⁻¹]

    # Wire thermal field
    wire_temperature: np.ndarray = field(
        default_factory=lambda: np.array([], dtype=np.float32)
    )
    time_in_critical_temp: int = 0
    wire_average_temperature: float | None = None  # computed each step

    # Spark state tuple: (state, y-loc, duration)
    # state: 0 = none | 1 = spark | −1 = short | −2 = rest
    spark_status: List[Optional[float]] = field(default_factory=lambda: [0, None, 0])

    # Dielectric
    dielectric_conductivity: float = (
        0.0  # [S m⁻¹] Conductivity of the dielectric material
    )
    dielectric_temperature: float = 0.0  # [K] Temperature of the dielectric material
    debris_concentration: float = (
        0.0  # [kg m⁻³] Concentration of debris in the dielectric
    )
    dielectric_flow_rate: float = 0.0  # [m³ s⁻¹] Flow rate of the dielectric
    ionized_channel: Optional[Tuple[float, int]] = (
        None  # (y-loc, duration) of the ionized channel
    )

    # Servo commands
    target_delta: float = 0.0  # [µm]
    target_position: float = 500.0  # [µm]

    # Process flags
    is_wire_broken: bool = False
    is_wire_colliding: bool = False
    is_target_distance_reached: bool = False
