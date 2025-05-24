#!/usr/bin/env python
# experiments/plot_temperature_heatmap.py
"""
Loads simulation log data (specifically time and wire temperature field)
and plots the wire temperature distribution as a heatmap over time,
along with the average wire temperature over time.

Usage:
    python experiments/plot_temperature_heatmap.py logs/smoke_test_wire_temps.npz
"""
import argparse
import numpy as np
import matplotlib.pyplot as plt
import pathlib


def plot_heatmap_and_average(npz_filepath: str):
    """
    Loads data from an .npz file and plots:
    1. The wire temperature distribution as a heatmap over time.
    2. The average wire temperature across all segments over time.

    Args:
        npz_filepath (str): Path to the .npz file containing simulation logs.
    """
    try:
        data = np.load(npz_filepath)
    except FileNotFoundError:
        print(f"Error: File not found at {npz_filepath}")
        return
    except Exception as e:
        print(f"Error loading .npz file: {e}")
        return

    if "time" not in data or "wire_temperature" not in data:
        print("Error: 'time' or 'wire_temperature' not found in the .npz file.")
        print(f"Available keys: {list(data.keys())}")
        return

    time_us = data["time"]
    wire_temp_field = data["wire_temperature"]  # Should be (n_timesteps, n_segments)

    if wire_temp_field.ndim != 2:
        print(
            f"Error: 'wire_temperature' data is not 2-dimensional (found {wire_temp_field.ndim} dimensions). Expected (timesteps, segments)."
        )
        return

    if len(time_us) != wire_temp_field.shape[0]:
        print(
            f"Error: Mismatch between number of time steps ({len(time_us)}) and temperature field rows ({wire_temp_field.shape[0]})."
        )
        return

    time_ms = time_us / 1000.0  # Convert time to milliseconds
    avg_temp_over_time = np.mean(
        wire_temp_field - 273.15, axis=1
    )  # Calculate average temperature across segments in Celsius

    n_segments = wire_temp_field.shape[1]
    segment_indices = np.arange(n_segments)

    # Create a figure with two subplots: heatmap on top, average temperature below
    fig, (ax_heatmap, ax_avg_temp) = plt.subplots(
        2,
        1,
        figsize=(10, 8),  # Adjusted figure size for two plots
        sharex=True,  # Share the x-axis (time)
        gridspec_kw={"height_ratios": [3, 1]},  # Heatmap gets more vertical space
        constrained_layout=True,  # Use constrained layout for better alignment
    )

    # Plot 1: Heatmap (on ax_heatmap)
    # Transpose wire_temp_field so segments are on y-axis and time on x-axis for imshow
    # imshow plots (M, N) data with M rows (y-axis) and N columns (x-axis)
    im = ax_heatmap.imshow(
        wire_temp_field.T,
        aspect="auto",
        origin="lower",  # Place segment 0 at the bottom
        extent=[
            time_ms[0],
            time_ms[-1],
            segment_indices[0] - 0.5,
            segment_indices[-1] + 0.5,
        ],  # Match axes
        interpolation="nearest",  # Good for discrete data
        vmin=20 + 273.15,  # Set minimum temperature to 20 C in Kelvin
        vmax=300 + 273.15,  # Set maximum temperature to 300 C in Kelvin
    )
    ax_heatmap.set_xlim(time_ms[0], time_ms[-1])  # Ensure time axis is aligned

    cbar = fig.colorbar(im, ax=ax_heatmap, label="Temperature (K)")
    ax_heatmap.set_ylabel("Wire Segment Index")
    ax_heatmap.set_title("Wire Temperature Distribution Over Time")

    # Plot 2: Average Temperature (on ax_avg_temp)
    ax_avg_temp.plot(time_ms, avg_temp_over_time, color="r", linestyle="-")
    ax_avg_temp.set_ylabel("Average Temp. (C)")
    ax_avg_temp.set_xlabel("Time (ms)")  # X-label for the bottom plot (shared axis)
    ax_avg_temp.grid(True)
    # ax_avg_temp.set_title("Average Wire Temperature Over Time") # Optional: title for this subplot

    # Ensure both axes share the exact same x-limits after all plotting.
    final_xlim = (time_ms[0], time_ms[-1])
    ax_heatmap.set_xlim(final_xlim)
    ax_avg_temp.set_xlim(final_xlim)  # Explicitly set for avg_temp too for robustness

    # plt.tight_layout() # Removed as constrained_layout is used
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Plot wire temperature heatmap and average temperature from simulation log."
    )
    parser.add_argument(
        "npz_file",
        type=str,
        help="Path to the .npz file containing logged simulation data (e.g., logs/smoke_test_wire_temps.npz)",
    )
    args = parser.parse_args()

    npz_file_path = pathlib.Path(args.npz_file)
    if not npz_file_path.is_file():
        print(f"Error: The provided path is not a file: {npz_file_path}")
    else:
        plot_heatmap_and_average(str(npz_file_path))
