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


def constant_gap_controller(env: WireEDMEnv, desired_gap: float = 15.0):
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


def run_episode(max_steps: int = 100_000, seed: int = 0, verbose: bool = False):
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

    for k in range(max_steps):
        action = constant_gap_controller(env)

        obs, rew, term, trunc, info = env.step(action)

        # ─── logging (only a few key signals for now) ───────────────────
        log["time"].append(env.state.time)
        log["voltage"].append(env.state.voltage or 0.0)
        log["current"].append(env.state.current or 0.0)
        log["wire_pos"].append(env.state.wire_position)
        log["workpiece_pos"].append(env.state.workpiece_position)

        if verbose and info["control_step"]:
            print(
                f"[{env.state.time/1000:.1f} ms] "
                f"gap={env.state.workpiece_position-env.state.wire_position:6.1f} µm   "
                f"V={env.state.voltage:6.1f}  I={env.state.current:6.1f}"
            )

        if term or trunc:
            reason = "target reached" if info["target_reached"] else "wire broken"
            print(f"\n💥 Terminated at t={env.state.time} µs ({reason}).")
            break

    sim_time = time.time() - t0
    print(
        f"Simulated {len(log['time']):,} µs in {sim_time:.2f} s "
        f"→ {len(log['time'])/sim_time/1e6:.1f} × realtime."
    )
    return log


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Wire-EDM smoke test")
    parser.add_argument(
        "--steps", type=int, default=100_000, help="µs to simulate (default: 100 000)"
    )
    parser.add_argument(
        "--plot", action="store_true", help="Show a quick Matplotlib plot at the end"
    )
    args = parser.parse_args()

    traces = run_episode(max_steps=args.steps)

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
