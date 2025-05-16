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


def constant_gap_controller(env: WireEDMEnv, desired_gap: float = 20.0):
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


def run_episode(max_steps: int = 1_000_000, seed: int = 0, verbose: bool = False):
    env = WireEDMEnv()
    env.reset(seed=seed)

    # handy initial conditions for testing
    env.state.workpiece_position = 100.0  # µm
    env.state.wire_position = 30.0  # µm
    env.state.target_position = 5_000.0  # µm

    # Initialize other state variables for safety
    env.state.spark_status = [0, None, 0]
    env.state.dielectric_temperature = 293.15  # Room temperature in K

    # Initialize the wire temperature array if not already
    if len(env.state.wire_temperature) == 0:
        env.wire.update(env.state)  # This should initialize the wire temperature array

    log = defaultdict(list)
    t0 = time.time()

    # Initialize action before the loop
    action = constant_gap_controller(env)

    for k in range(max_steps):
        # action = constant_gap_controller(env) # Old: called every step

        obs, rew, term, trunc, info = env.step(action)

        # If a control step was just processed, get the next action
        if info.get("control_step", False):  # Use .get for safety
            action = constant_gap_controller(env)

        # ─── logging (only a few key signals for now) ───────────────────
        log["time"].append(env.state.time)
        log["voltage"].append(env.state.voltage or 0.0)
        log["current"].append(env.state.current or 0.0)
        log["wire_pos"].append(env.state.wire_position)
        log["workpiece_pos"].append(env.state.workpiece_position)

        if (
            verbose and info["control_step"]
        ):  # Note: 'control_step' might not be in info
            print(
                f"[{env.state.time/1000:.1f} ms] "
                f"gap={env.state.workpiece_position-env.state.wire_position:6.1f} µm   "
                f"V={env.state.voltage:6.1f}  I={env.state.current:6.1f}"
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

    total_simulated_us = 0
    if log["time"]:  # Ensure log["time"] is not empty
        total_simulated_us = log["time"][-1]  # Actual total simulated time in µs

    # Original print statement in run_episode, using total_simulated_us
    if sim_time_wall_clock > 0 and total_simulated_us > 0:
        speed_factor = (
            total_simulated_us / sim_time_wall_clock / 1e6
        )  # sim_seconds / real_seconds
        print(
            f"Simulated {total_simulated_us:,} µs ({total_simulated_us / 1e3:.2f} ms) in {sim_time_wall_clock:.2f} s "
            f"→ {speed_factor:.1f} × realtime."
        )
    elif total_simulated_us > 0:  # sim_time_wall_clock is <= 0
        print(
            f"Simulated {total_simulated_us:,} µs ({total_simulated_us / 1e3:.2f} ms) in {sim_time_wall_clock:.2f} s. "
            "(Wall clock time too short to calculate speed factor reliably)."
        )
    else:  # total_simulated_us is 0
        print(
            f"Simulation ran for {sim_time_wall_clock:.2f} s, but no simulation steps were logged or simulation time was zero."
        )

    return log, sim_time_wall_clock, total_simulated_us


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
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

    traces, wall_time_s, sim_time_us = run_episode(
        max_steps=args.steps, verbose=args.verbose
    )

    # New print statement for performance metric: real seconds per simulated second
    if sim_time_us > 0 and wall_time_s > 0:
        sim_time_s = sim_time_us / 1_000_000.0
        wall_time_per_sim_time = wall_time_s / sim_time_s
        print(
            f"Performance: {wall_time_per_sim_time:.3f} wall-clock seconds per simulated second."
        )
    elif sim_time_us == 0:
        print("Cannot calculate performance: Total simulated time is zero.")
    # wall_time_s <= 0 is unlikely if sim_time_us > 0, but handle defensively
    elif wall_time_s <= 0 and sim_time_us > 0:
        print("Cannot calculate performance: Wall-clock time is zero or negative.")

    if args.plot:
        import matplotlib.pyplot as plt

        t_ms = np.array(traces["time"]) / 1000.0
        fig, ax = plt.subplots(3, 1, sharex=True, figsize=(9, 8))

        ax[0].plot(t_ms, traces["voltage"], label="Voltage [V]")
        ax[0].plot(t_ms, traces["current"], label="Current [A]")
        ax[0].set_ylabel("Electrical")
        ax[0].legend()

        ax[1].plot(t_ms, np.array(traces["wire_pos"]), label="Wire pos")
        ax[1].plot(t_ms, np.array(traces["workpiece_pos"]), label="Workpiece pos")
        ax[1].set_ylabel("Position [µm]")
        ax[1].legend()

        gap = np.array(traces["workpiece_pos"]) - np.array(traces["wire_pos"])
        ax[2].plot(t_ms, gap, label="Gap")
        ax[2].set_ylabel("Gap [µm]")
        ax[2].set_xlabel("time [ms]")
        ax[2].legend()

        plt.tight_layout()
        plt.show()
