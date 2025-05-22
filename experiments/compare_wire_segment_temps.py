#!/usr/bin/env python
# experiments/compare_wire_segment_temps.py
"""
Loads simulation log data for different wire segment sizes and creates
a comparison plot of wire temperature over time.

Usage:
    python experiments/compare_wire_segment_temps.py
"""
import argparse
import numpy as np
import matplotlib.pyplot as plt
import pathlib
from matplotlib.cm import get_cmap


def plot_segment_comparison(
    save_plot: bool = False,
    output_filename: str = "wire_segment_comparison.png",
    workpiece_midpoint: bool = False,
):
    """
    Loads data from multiple .npz files with different segment sizes and
    creates a comparison plot of wire temperature over time.

    Args:
        save_plot (bool): Whether to save the plot to a file.
        output_filename (str): Filename for the saved plot.
        workpiece_midpoint (bool): If True, plot temperature at workpiece midpoint.
                                  If False, plot maximum temperature in workpiece region.
    """
    # Segment sizes available in the logs folder
    segment_sizes = [0.1, 0.15, 0.2, 0.25, 0.5, 1.0]

    # Setup the plot
    plt.figure(figsize=(12, 8))
    plt.title("Wire Temperature Comparison Across Different Segment Sizes")
    plt.xlabel("Time (ms)")
    plt.ylabel("Temperature (°C)")
    plt.grid(True, alpha=0.3)

    # Get a colormap for different segment sizes
    cmap = get_cmap("viridis")
    colors = [cmap(i / len(segment_sizes)) for i in range(len(segment_sizes))]

    # Physical dimensions based on src/wedm/modules/wire.py and src/wedm/envs/wire_edm.py
    actual_workpiece_height_mm = 50.0  # From wire_edm.py: env.workpiece_height
    buffer_bottom_mm = 30.0  # From wire.py: buffer_len_bottom
    workpiece_bottom_y = buffer_bottom_mm
    workpiece_top_y = buffer_bottom_mm + actual_workpiece_height_mm

    # Define rolling average window size
    rolling_avg_window_size = 1000  # Number of timesteps for the rolling average

    for i, segment_size in enumerate(segment_sizes):
        # Construct file path
        file_path = (
            f"logs/smoke_test_wire_temps_{segment_size:.2f}".replace(".00", "").replace(
                ".", "_"
            )
            + ".npz"
        )

        try:
            # Load data
            data = np.load(file_path)

            if "time" not in data or "wire_temperature" not in data:
                print(f"Error: 'time' or 'wire_temperature' not found in {file_path}")
                continue

            time_us = data["time"]
            wire_temp_field_k = data["wire_temperature"]  # (n_timesteps, n_segments)

            # Convert time to milliseconds and temperature to Celsius
            time_ms = time_us / 1000.0
            wire_temp_field_c = wire_temp_field_k - 273.15

            # Get the number of segments
            n_timesteps, n_segments = wire_temp_field_c.shape

            # Calculate the physical y-position of each segment
            # Assuming total wire length is 100mm as per original code comment
            total_wire_length_mm = 100.0
            # Calculate segment length based on loaded data, not assumed total length
            # This is more robust if total length changes in logs
            # However, the original code assumes 100mm, let's stick to that for consistency with y_positions calculation
            # segment_length_from_data = total_wire_length_mm / n_segments
            y_positions = np.linspace(0, total_wire_length_mm, n_segments)

            # Identify segments within workpiece region
            workpiece_mask = (y_positions >= workpiece_bottom_y) & (
                y_positions <= workpiece_top_y
            )

            if workpiece_midpoint:
                # Find segment closest to workpiece midpoint
                midpoint_y = (workpiece_bottom_y + workpiece_top_y) / 2
                midpoint_idx = np.argmin(np.abs(y_positions - midpoint_y))
                # Extract temperature at midpoint over time
                temp_over_time = wire_temp_field_c[:, midpoint_idx]
                location_desc = "at workpiece midpoint"
            else:
                # Extract maximum temperature in workpiece region at each timestep
                # Ensure workpiece_mask is not empty
                if not np.any(workpiece_mask):
                    print(
                        f"Warning: No segments found in workpiece region for {file_path}. Skipping."
                    )
                    continue
                temp_over_time = np.max(wire_temp_field_c[:, workpiece_mask], axis=1)
                location_desc = "max in workpiece region"

            # Plot this segment size
            # plt.plot(
            #     time_ms,
            #     temp_over_time,
            #     label=f"Segment size: {segment_size} mm",
            #     color=colors[i],
            #     linewidth=2,
            # )

            # Calculate and plot rolling average
            if len(temp_over_time) >= rolling_avg_window_size:
                kernel = np.ones(rolling_avg_window_size) / rolling_avg_window_size
                rolling_avg = np.convolve(
                    temp_over_time, kernel, mode="valid"
                )  # Use 'valid' to avoid edge effects
                # Adjust time_ms for 'valid' mode
                time_ms_avg = time_ms[rolling_avg_window_size - 1 :]

                # Plot rolling average
                plt.plot(
                    time_ms_avg,
                    rolling_avg,
                    color=colors[i],
                    linestyle="-",
                    linewidth=2,
                    label=f"Segment size: {segment_size} mm",
                )
            else:
                print(
                    f"Warning: Not enough data points ({len(temp_over_time)}) for rolling average window size ({rolling_avg_window_size}) for {file_path}. Skipping rolling average plot."
                )

            print(
                f"Processed {file_path}: {n_segments} segments, max temp: {np.max(temp_over_time):.2f}°C"
            )

        except FileNotFoundError:
            print(f"Warning: File not found: {file_path}")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    plt.legend()

    if save_plot:
        try:
            plt.savefig(output_filename, dpi=300, bbox_inches="tight")
            print(f"Plot saved to {output_filename}")
        except Exception as e:
            print(f"Error saving plot: {e}")

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compare wire temperatures across different segment sizes."
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save the plot to a file instead of just displaying it.",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="wire_segment_comparison.png",
        help="Output filename for the saved plot (e.g., comparison.png)",
    )
    parser.add_argument(
        "--midpoint",
        action="store_true",
        help="Plot temperature at workpiece midpoint instead of maximum temperature",
    )
    args = parser.parse_args()

    plot_segment_comparison(
        save_plot=args.save, output_filename=args.out, workpiece_midpoint=args.midpoint
    )
