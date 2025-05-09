# src/edm_env/__init__.py
from importlib.metadata import version, PackageNotFoundError

__all__ = ["WireEDMEnv", "EDMState"]

from .envs.wire_edm import WireEDMEnv
from .core.state import EDMState

try:
    __version__ = version("wedm") if "__package__" in globals() else "0.dev"
except PackageNotFoundError:
    __version__ = "0.dev"
