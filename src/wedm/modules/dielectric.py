# src/edm_env/modules/dielectric.py
from __future__ import annotations

from ..core.module import EDMModule
from ..core.state import EDMState


class DielectricModule(EDMModule):
    """Tracks debris concentration & ionised channel lifetime."""

    beta = 1e-3     # debris ↑ per mm³ crater
    gamma = 5e-4    # base decay rate (µs⁻¹)
    tau_deion = 6   # µs

    def __init__(self, env):
        super().__init__(env)
        self.temp_K = 293.15
        self.debris = 0.0
        self.flow_rate = 1.0
        self.ion_channel = None         # (y, remaining µs)

    # ------------------------------------------------------------------ #
    def update(self, state: EDMState) -> None:
        state.dielectric_temperature = self.temp_K

        # Add debris on spark birth
        if state.spark_status[0] == 1 and state.spark_status[2] == 0:
            crater_vol = 0.1  # placeholder mm³
            self.debris = min(1.0, self.debris + self.beta * crater_vol)
            self.ion_channel = (state.spark_status[1], self.tau_deion)

        # Ionised channel lifetime
        if self.ion_channel:
            y_loc, t_left = self.ion_channel
            self.ion_channel = (y_loc, t_left - 1) if t_left > 1 else None

        # Debris flushing (exp. decay)
        self.debris *= 1 - self.gamma * self.flow_rate
        self.debris = max(0.0, self.debris)

        # Sync back to global state
        state.debris_concentration = self.debris
        state.flow_rate = self.flow_rate
        state.ionized_channel = self.ion_channel
