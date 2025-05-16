# src/edm_env/modules/material.py
from __future__ import annotations

from ..core.module import EDMModule
from ..core.state import EDMState


class MaterialRemovalModule(EDMModule):
    """Very simple deterministic material-removal stub."""

    def update(self, state: EDMState) -> None:
        if state.spark_status[0] == 1 and state.spark_status[2] == 0:
            # constant 0.05 mm per fresh spark
            state.workpiece_position += 0.0005
