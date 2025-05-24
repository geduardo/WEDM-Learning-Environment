#!/usr/bin/env python
# experiments/smoke_test.py
"""
Quick-n-dirty simulation run to be sure everything wires together.
Run:
    python experiments/smoke_test.py --steps 200000 --plot
"""
from __future__ import annotations

import argparse
import time
from collections import defaultdict

import numpy as np

# Make "import edm_env" work if you haven't installed the package yet
import sys, pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from src.wedm.envs import WireEDMEnv
from src.wedm.utils.logger import (
    SimulationLogger,
    LoggerConfig,
    LogFrequencyControlStep,
    BackendMemory,
)


def constant_gap_controller(env: WireEDMEnv, desired_gap: float = 17.0):
    """Very naive hand-crafted policy ↩ returns a Gym-style action dict."""
    delta = env.state.workpiece_position - desired_gap - env.state.wire_position
    return {
        "servo": np.array([delta], dtype=np.float32),
        "generator_control": {
            "target_voltage": np.array([80.0], dtype=np.float32),
            "peak_current": np.array([300.0], dtype=np.float32),
            "ON_time": np.array([2.0], dtype=np.float32),
            "OFF_time": np.array([5.0], dtype=np.float32),
        },
    }


def run_episode(
    max_steps: int = 10_000_000,
    seed: int = 0,
    verbose: bool = False,
    logger_config: LoggerConfig | None = None,
):
    env = WireEDMEnv()
    env.reset(seed=seed)

    # handy initial conditions for testing
    env.state.workpiece_position = 100.0  # µm
    env.state.wire_position = 30.0  # µm
    env.state.target_position = 5_000.0  # µm

    # Initialize other state variables for safety
    env.state.spark_status = [0, None, 0]
    env.state.dielectric_temperature = 293.15  # Room temperature in K
    env.state.wire_average_temperature = env.state.dielectric_temperature

    # Initialize the wire temperature array if not already
    if len(env.state.wire_temperature) == 0:
        env.wire.update(env.state)  # This should initialize the wire temperature array

    # --- Logger Configuration & Initialization ---
    if (
        logger_config is None
    ):  # Default config if none provided (e.g. for other callers)
        logger_config: LoggerConfig = {
            "signals_to_log": ["time"],
            "log_frequency": {"type": "control_step"},
            "backend": {"type": "memory"},
        }

    logger = SimulationLogger(config=logger_config, env_reference=env)
    logger.reset()

    t0 = time.time()

    # Initialize action before the loop
    action = constant_gap_controller(env)

    for k in range(max_steps):
        obs, rew, term, trunc, info = env.step(action)

        # Log data using the new logger
        logger.collect(env.state, info)

        # If a control step was just processed, get the next action
        if info.get("control_step", False):  # Use .get for safety
            action = constant_gap_controller(env)

        # ─── logging (only a few key signals for now) ───────────────────
        if verbose and info.get("control_step", False):
            print(
                f"[{env.state.time/1000:.1f} ms] "
                f"gap={env.state.workpiece_position-env.state.wire_position:6.1f} µm   "
                f"V={env.state.voltage or 0.0:6.1f}  I={env.state.current or 0.0:6.1f}  "
                f"AvgWireT={env.state.wire_average_temperature or 0.0:6.1f} K"
            )

        if term or trunc:
            # Original logic for determining reason string
            reason_str = "unknown"
            if info.get("target_reached", False):
                reason_str = "target reached"
            elif info.get("wire_broken", False):
                reason_str = "wire broken"
            elif term:
                reason_str = "terminated"
            elif trunc:
                reason_str = "truncated"
            print(f"\n💥 Terminated at t={env.state.time} µs ({reason_str}).")
            break

    sim_time_wall_clock = time.time() - t0
    logger.finalize()
    returned_log_data = (
        logger.get_data()
    )  # Get data from logger (dict or filepath string)

    # Calculate total_simulated_us from the perspective of run_episode (before potential npz load)
    # This helps in case the main function can't load/access the npz for some reason.
    total_simulated_us_internal = 0
    current_data_for_calc = None
    if logger_config["backend"]["type"] == "memory":
        current_data_for_calc = returned_log_data
    elif logger_config["backend"]["type"] == "numpy" and isinstance(
        returned_log_data, str
    ):
        # Attempt to load for internal calculation if numpy, but prioritize main's loading
        try:
            current_data_for_calc = np.load(returned_log_data)
        except:
            current_data_for_calc = None  # Could not load, will rely on main

    if (
        current_data_for_calc
        and "time" in current_data_for_calc
        and len(current_data_for_calc["time"]) > 0
    ):
        total_simulated_us_internal = current_data_for_calc["time"][-1]

    # Original print statement in run_episode, using total_simulated_us_internal
    if sim_time_wall_clock > 0 and total_simulated_us_internal > 0:
        speed_factor = (
            total_simulated_us_internal / sim_time_wall_clock / 1e6
        )  # sim_seconds / real_seconds
        print(
            f"Simulated {total_simulated_us_internal:,} µs ({total_simulated_us_internal / 1e3:.2f} ms) in {sim_time_wall_clock:.2f} s "
            f"→ {speed_factor:.1f} × realtime."
        )
    elif total_simulated_us_internal > 0:  # sim_time_wall_clock is <= 0
        print(
            f"Simulated {total_simulated_us_internal:,} µs ({total_simulated_us_internal / 1e3:.2f} ms) in {sim_time_wall_clock:.2f} s. "
            "(Wall clock time too short to calculate speed factor reliably)."
        )
    else:  # total_simulated_us is 0
        print(
            f"Simulation ran for {sim_time_wall_clock:.2f} s, but no simulation steps were logged or simulation time was zero for internal check."
        )

    return returned_log_data, sim_time_wall_clock, total_simulated_us_internal


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def main():  # Define a main function to encapsulate the script logic
    parser = argparse.ArgumentParser(description="Wire-EDM smoke test")
    parser.add_argument(
        "--steps", type=int, default=1_000_000, help="µs to simulate (default: 100 000)"
    )
    parser.add_argument(
        "--plot", action="store_true", help="Show a quick Matplotlib plot at the end"
    )
    # Add verbose argument for consistency, though not strictly required by prompt
    parser.add_argument(
        "--verbose", action="store_true", help="Print verbose output during simulation"
    )
    args = parser.parse_args()

    # Determine logger config based on args or defaults
    # This allows for easier switching if we add cmd args for logger backend later
    logger_config_main: LoggerConfig = {
        "signals_to_log": [
            "time",
            "voltage",
            "current",
            "wire_position",
            "workpiece_position",
            "wire_average_temperature",
            "wire_temperature",
        ],
        "log_frequency": {"type": "every_step"},
        "backend": {
            "type": "numpy",
            "filepath": "logs/smoke_test_wire_temps.npz",
            "compress": True,
        },
    }

    # Pass the chosen logger_config to run_episode
    # run_episode will instantiate the logger with this config
    returned_data_or_filepath, wall_time_s, sim_time_us_calculated = run_episode(
        max_steps=args.steps, verbose=args.verbose, logger_config=logger_config_main
    )

    # Handle returned data based on logger backend
    actual_traces = None
    if logger_config_main["backend"]["type"] == "memory":
        actual_traces = returned_data_or_filepath  # This is the dict of lists
    elif logger_config_main["backend"]["type"] == "numpy":
        if returned_data_or_filepath and isinstance(returned_data_or_filepath, str):
            try:
                actual_traces = np.load(
                    returned_data_or_filepath
                )  # Load data from .npz file
                print(f"Successfully loaded data from {returned_data_or_filepath}")
            except Exception as e:
                print(f"Error loading .npz file {returned_data_or_filepath}: {e}")
                actual_traces = None  # Ensure it's None if loading fails
        else:
            print(
                "Numpy backend selected, but no valid filepath was returned from logger."
            )

    # Recalculate total_simulated_us based on actual_traces if they exist
    # This was previously done in run_episode, but run_episode now returns the raw data or path
    total_simulated_us = 0
    if actual_traces and "time" in actual_traces and len(actual_traces["time"]) > 0:
        total_simulated_us = actual_traces["time"][-1]
    elif (
        sim_time_us_calculated > 0
    ):  # Fallback if direct trace access fails but run_episode had a value
        total_simulated_us = sim_time_us_calculated
        print(
            "Warning: Used total_simulated_us from run_episode as direct trace access failed post-load."
        )

    # Performance printout (using potentially re-evaluated total_simulated_us)
    if (
        sim_time_us_calculated > 0 and wall_time_s > 0
    ):  # Use original sim_time_us for this metric for consistency
        sim_time_s = sim_time_us_calculated / 1_000_000.0
        wall_time_per_sim_time = wall_time_s / sim_time_s
        print(
            f"Performance: {wall_time_per_sim_time:.3f} wall-clock seconds per simulated second."
        )
    elif sim_time_us_calculated == 0:
        print(
            "Cannot calculate performance: Total simulated time from run_episode is zero."
        )
    elif wall_time_s <= 0 and sim_time_us_calculated > 0:
        print("Cannot calculate performance: Wall-clock time is zero or negative.")

    if args.plot:
        import matplotlib.pyplot as plt

        # Fix the condition to properly handle both dict and numpy objects
        has_valid_data = False
        if actual_traces is not None:
            if (
                isinstance(actual_traces, dict)
                and "time" in actual_traces
                and len(actual_traces["time"]) > 0
            ):
                has_valid_data = True
            elif (
                hasattr(actual_traces, "keys")
                and "time" in actual_traces.keys()
                and len(actual_traces["time"]) > 0
            ):
                has_valid_data = True

        if not has_valid_data:
            print(
                "No data available for plotting, or 'time' signal missing/empty. Skipping plot."
            )
            return

        t_ms = np.array(actual_traces["time"]) / 1000.0
        # Adjust subplot to include wire temperature
        fig, ax = plt.subplots(
            4, 1, sharex=True, figsize=(9, 10)
        )  # Changed to 4 subplots

        # Ensure signals exist in traces before trying to plot them
        if "voltage" in actual_traces:
            ax[0].plot(t_ms, actual_traces["voltage"], label="Voltage [V]")
        if "current" in actual_traces:
            ax[0].plot(t_ms, actual_traces["current"], label="Current [A]")
        ax[0].set_ylabel("Electrical")
        ax[0].legend()

        if "wire_position" in actual_traces:
            ax[1].plot(t_ms, np.array(actual_traces["wire_position"]), label="Wire pos")
        if "workpiece_position" in actual_traces:
            ax[1].plot(
                t_ms,
                np.array(actual_traces["workpiece_position"]),
                label="Workpiece pos",
            )
        ax[1].set_ylabel("Position [µm]")
        ax[1].legend()

        if "workpiece_position" in actual_traces and "wire_position" in actual_traces:
            gap = np.array(actual_traces["workpiece_position"]) - np.array(
                actual_traces["wire_position"]
            )
            ax[2].plot(t_ms, gap, label="Gap")
        ax[2].set_ylabel("Gap [µm]")
        ax[2].legend()

        # New subplot for average wire temperature
        if "wire_average_temperature" in actual_traces:
            ax[3].plot(
                t_ms,
                np.array(actual_traces["wire_average_temperature"]) - 273.15,
                label="Avg Wire Temp (Work Zone) [°C]",
            )
        ax[3].set_ylabel("Avg Wire Temp [°C]")
        ax[3].set_xlabel("time [ms]")
        ax[3].legend()

        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    main()  # Call the main function
