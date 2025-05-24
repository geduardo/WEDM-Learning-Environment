#!/usr/bin/env python
# experiments/smoke_test.py
"""
Quick-n-dirty simulation run to be sure everything wires together.
Run:
    python experiments/smoke_test.py --steps 200000 --plot
    python experiments/smoke_test.py --steps 200000 --plot --mode velocity
"""
from __future__ import annotations

import argparse
import time
from typing import Dict, Any, Tuple, Optional

import numpy as np
import sys, pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from src.wedm.envs import WireEDMEnv
from src.wedm.utils.logger import SimulationLogger, LoggerConfig


def create_gap_controller(desired_gap: float = 17.0):  # µm
    """Create adaptive gap controller that works with both control modes."""

    def controller(env: WireEDMEnv) -> Dict[str, Any]:
        gap = env.state.workpiece_position - env.state.wire_position
        error = gap - desired_gap

        if env.mechanics.control_mode == "position":
            # Position control: return position increment [µm]
            delta = error * 0.1  # Conservative proportional gain
        else:  # velocity control
            # Velocity control: return target velocity [µm/s]
            delta = error * 50.0  # Higher gain for velocity control
            delta = np.clip(delta, -1000.0, 1000.0)  # Limit velocity command

        return {
            "servo": np.array([delta], dtype=np.float32),
            "generator_control": {
                "target_voltage": np.array([80.0], dtype=np.float32),
                "peak_current": np.array([300.0], dtype=np.float32),
                "ON_time": np.array([2.0], dtype=np.float32),
                "OFF_time": np.array([5.0], dtype=np.float32),
            },
        }

    return controller


def setup_logger(control_mode: str, log_to_file: bool = True) -> LoggerConfig:
    """Setup logger configuration."""
    signals_to_log = [
        "time",
        "voltage",
        "current",
        "wire_position",
        "wire_velocity",
        "workpiece_position",
        "wire_average_temperature",
        "wire_temperature",
        "target_delta",
    ]

    if log_to_file:
        return {
            "signals_to_log": signals_to_log,
            "log_frequency": {"type": "every_step"},
            "backend": {
                "type": "numpy",
                "filepath": f"logs/smoke_test_{control_mode}_control.npz",
                "compress": True,
            },
        }
    else:
        return {
            "signals_to_log": ["time"],
            "log_frequency": {"type": "control_step"},
            "backend": {"type": "memory"},
        }


def initialize_environment(control_mode: str, seed: int = 0) -> WireEDMEnv:
    """Initialize and setup the EDM environment."""
    env = WireEDMEnv(mechanics_control_mode=control_mode)
    env.reset(seed=seed)

    # Set initial conditions
    env.state.workpiece_position = 100.0  # µm
    env.state.wire_position = 30.0  # µm
    env.state.target_position = 5_000.0  # µm
    env.state.spark_status = [0, None, 0]
    env.state.dielectric_temperature = 293.15  # Room temperature in K
    env.state.wire_average_temperature = env.state.dielectric_temperature

    # Initialize wire temperature array
    if len(env.state.wire_temperature) == 0:
        env.wire.update(env.state)

    return env


def run_simulation(
    env: WireEDMEnv, max_steps: int, verbose: bool, logger_config: LoggerConfig
) -> Tuple[Any, float, int]:
    """Run the core simulation loop."""
    print(
        f"🔧 Running smoke test with {env.mechanics.control_mode.upper()} control mode"
    )

    logger = SimulationLogger(config=logger_config, env_reference=env)
    logger.reset()

    controller = create_gap_controller()
    action = controller(env)

    start_time = time.time()

    for step in range(max_steps):
        # Run the simulation step
        obs, reward, terminated, truncated, info = env.step(action)
        logger.collect(env.state, info)

        # Update action on control steps
        if info.get("control_step", False):
            action = controller(env)

            if verbose:
                print_step_info(env, step)

        # Check termination
        if terminated or truncated:
            reason = get_termination_reason(info, terminated, truncated)
            print(f"\n💥 Terminated at t={env.state.time} µs ({reason}).")
            break

    wall_time = time.time() - start_time
    logger.finalize()
    log_data = logger.get_data()

    # Calculate simulation time
    sim_time_us = get_simulation_time(log_data, logger_config)
    print_performance_summary(sim_time_us, wall_time)

    return log_data, wall_time, sim_time_us


def print_step_info(env: WireEDMEnv, step: int) -> None:
    """Print verbose step information."""
    gap = env.state.workpiece_position - env.state.wire_position
    target_unit = "µm" if env.mechanics.control_mode == "position" else "µm/s"

    print(
        f"[{env.state.time/1000:.1f} ms] "
        f"gap={gap:6.1f} µm   "
        f"target_delta={env.state.target_delta:6.1f} {target_unit}   "
        f"wire_vel={env.state.wire_velocity:6.1f} µm/s   "
        f"V={env.state.voltage or 0.0:6.1f}  I={env.state.current or 0.0:6.1f}  "
        f"AvgWireT={env.state.wire_average_temperature or 0.0:6.1f} K"
    )


def get_termination_reason(info: Dict, terminated: bool, truncated: bool) -> str:
    """Determine termination reason."""
    if info.get("target_reached", False):
        return "target reached"
    elif info.get("wire_broken", False):
        return "wire broken"
    elif terminated:
        return "terminated"
    elif truncated:
        return "truncated"
    else:
        return "unknown"


def get_simulation_time(log_data: Any, logger_config: LoggerConfig) -> int:
    """Extract simulation time from log data."""
    if logger_config["backend"]["type"] == "memory":
        data = log_data
    else:  # numpy backend
        try:
            data = np.load(log_data) if isinstance(log_data, str) else None
        except:
            data = None

    if data and "time" in data and len(data["time"]) > 0:
        return int(data["time"][-1])
    return 0


def print_performance_summary(sim_time_us: int, wall_time: float) -> None:
    """Print simulation performance summary."""
    if wall_time > 0 and sim_time_us > 0:
        speed_factor = sim_time_us / wall_time / 1e6  # sim_seconds / real_seconds
        print(
            f"Simulated {sim_time_us:,} µs ({sim_time_us / 1e3:.2f} ms) "
            f"in {wall_time:.2f} s → {speed_factor:.1f}× realtime."
        )

        sim_time_s = sim_time_us / 1_000_000.0
        wall_time_per_sim_time = wall_time / sim_time_s
        print(
            f"Performance: {wall_time_per_sim_time:.3f} wall-clock seconds per simulated second."
        )
    else:
        print(f"Simulation completed in {wall_time:.2f} s")


def load_simulation_data(log_data: Any, logger_config: LoggerConfig) -> Optional[Any]:
    """Load and return simulation data for plotting."""
    if logger_config["backend"]["type"] == "memory":
        return log_data
    elif logger_config["backend"]["type"] == "numpy" and isinstance(log_data, str):
        try:
            data = np.load(log_data)
            print(f"Successfully loaded data from {log_data}")
            return data
        except Exception as e:
            print(f"Error loading .npz file {log_data}: {e}")
            return None
    else:
        print("No valid data available for plotting.")
        return None


def plot_simulation_results(data: Any, control_mode: str) -> None:
    """Create comprehensive plots of simulation results."""
    import matplotlib.pyplot as plt

    # Validate data
    if not data or "time" not in data or len(data["time"]) == 0:
        print("No valid data available for plotting.")
        return

    t_ms = np.array(data["time"]) / 1000.0
    target_unit = "µm" if control_mode == "position" else "µm/s"

    fig, axes = plt.subplots(5, 1, sharex=True, figsize=(10, 12))

    # Position the plot window in the center of the screen
    try:
        mngr = fig.canvas.manager
        # Try different backends
        if hasattr(mngr, "window"):
            if hasattr(mngr.window, "wm_geometry"):
                # Tkinter backend
                mngr.window.wm_geometry(
                    "+100+50"
                )  # x_offset=100, y_offset=50 from top-left
            elif hasattr(mngr.window, "setGeometry"):
                # Qt backend
                mngr.window.setGeometry(100, 50, 1000, 800)  # x, y, width, height
    except:
        # If positioning fails, just continue without it
        pass

    # 1. Electrical signals
    if "voltage" in data:
        axes[0].plot(t_ms, data["voltage"], label="Voltage [V]", color="blue")
    if "current" in data:
        axes[0].plot(t_ms, data["current"], label="Current [A]", color="red")
    axes[0].set_ylabel("Electrical")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # 2. Positions
    if "wire_position" in data:
        axes[1].plot(t_ms, data["wire_position"], label="Wire pos", color="blue")
    if "workpiece_position" in data:
        axes[1].plot(
            t_ms, data["workpiece_position"], label="Workpiece pos", color="orange"
        )
    axes[1].set_ylabel("Position [µm]")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    # 3. Wire velocity
    if "wire_velocity" in data:
        axes[2].plot(t_ms, data["wire_velocity"], label="Wire velocity", color="green")
    axes[2].set_ylabel("Velocity [µm/s]")
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)

    # 4. Gap and control signal
    if "workpiece_position" in data and "wire_position" in data:
        gap = np.array(data["workpiece_position"]) - np.array(data["wire_position"])
        axes[3].plot(t_ms, gap, label="Gap", color="blue", linewidth=2)
    if "target_delta" in data:
        axes[3].plot(
            t_ms,
            data["target_delta"],
            label=f"Target delta [{target_unit}]",
            color="red",
            linestyle="--",
            alpha=0.7,
        )
    axes[3].axhline(y=17.0, color="k", linestyle=":", alpha=0.5, label="Desired gap")
    axes[3].set_ylabel(f"Gap [µm] / Target [{target_unit}]")
    axes[3].legend()
    axes[3].grid(True, alpha=0.3)

    # 5. Wire temperature
    if "wire_average_temperature" in data:
        temp_celsius = np.array(data["wire_average_temperature"]) - 273.15
        axes[4].plot(
            t_ms, temp_celsius, label="Avg Wire Temp (Work Zone)", color="purple"
        )
    axes[4].set_ylabel("Temperature [°C]")
    axes[4].set_xlabel("Time [ms]")
    axes[4].legend()
    axes[4].grid(True, alpha=0.3)

    plt.suptitle(
        f"Wire-EDM Smoke Test ({control_mode.capitalize()} Control)",
        fontsize=14,
        fontweight="bold",
    )
    plt.tight_layout()
    plt.show()


def main():
    """Main entry point with clean CLI handling."""
    parser = argparse.ArgumentParser(description="Wire-EDM smoke test")
    parser.add_argument(
        "--steps", type=int, default=200_000, help="µs to simulate (default: 200,000)"
    )
    parser.add_argument("--plot", action="store_true", help="Show plots at the end")
    parser.add_argument(
        "--verbose", action="store_true", help="Print verbose output during simulation"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["position", "velocity"],
        default="position",
        help="Mechanics control mode (default: position)",
    )

    args = parser.parse_args()

    # Setup
    logger_config = setup_logger(args.mode, log_to_file=True)
    env = initialize_environment(args.mode, seed=0)

    # Run simulation
    log_data, wall_time, sim_time_us = run_simulation(
        env, args.steps, args.verbose, logger_config
    )

    # Plotting
    if args.plot:
        data = load_simulation_data(log_data, logger_config)
        if data is not None:
            plot_simulation_results(data, args.mode)


if __name__ == "__main__":
    main()
