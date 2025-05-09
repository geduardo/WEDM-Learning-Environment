# src/edm_env/__init__.py
from importlib.metadata import version

__all__ = ["WireEDMEnv", "EDMState"]

from .envs.wire_edm import WireEDMEnv
from .core.state import EDMState

__version__ = version("edm_env") if "__package__" in globals() else "0.dev"