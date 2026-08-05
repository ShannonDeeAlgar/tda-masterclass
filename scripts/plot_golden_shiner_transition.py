#!/usr/bin/env python3
"""Plot the empirical golden-shiner transition retained for the Reader."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


OBSERVATIONS = Path("data/golden_shiner_transition_observations.csv")
FRAMES = Path("data/golden_shiner_transition_frames.csv")
OUTPUT = Path("assets/golden-shiner-transition.svg")
SNAPSHOTS = (0, 80, 152)

observations = pd.read_csv(OBSERVATIONS)
frames = pd.read_csv(FRAMES)

fig = plt.figure(figsize=(13, 6.6), constrained_layout=True)
grid = fig.add_gridspec(2, 3, height_ratios=(1.35, 1))
snapshot_axes = [fig.add_subplot(grid[0, column]) for column in range(3)]
series = fig.add_subplot(grid[1, :])

for axis, teaching_frame in zip(snapshot_axes, SNAPSHOTS):
    points = observations[observations.teaching_frame == teaching_frame]
    state = frames.loc[frames.teaching_frame == teaching_frame].iloc[0]
    axis.scatter(
        points.x_px,
        points.y_px,
        s=12,
        color="#23658a",
        alpha=0.82,
        linewidths=0,
    )
    axis.quiver(
        points.x_px,
        points.y_px,
        points.vx_source,
        points.vy_source,
        color="#9b3d3d",
        alpha=0.34,
        scale=35,
        width=0.003,
    )
    axis.set_title(
        f'{state.time_s:.1f} s: {state.published_state_rule}\n'
        f'$P={state.polarisation:.2f}$, $R={state.rotation:.2f}$, '
        f'$n={int(state.n_detected)}$'
    )
    axis.set_xlim(420, 1880)
    axis.set_ylim(870, 80)
    axis.set_aspect("equal")
    axis.set_xlabel("camera x (pixels)")
    if axis is snapshot_axes[0]:
        axis.set_ylabel("camera y (pixels)")
    else:
        axis.set_yticklabels([])

series.plot(
    frames.time_s,
    frames.polarisation,
    color="#23658a",
    linewidth=2,
    label="polarisation $P$",
)
series.plot(
    frames.time_s,
    frames.rotation,
    color="#9b3d3d",
    linewidth=2,
    label="collective rotation $R$",
)
for teaching_frame in SNAPSHOTS:
    time = frames.loc[frames.teaching_frame == teaching_frame, "time_s"].iloc[0]
    series.axvline(time, color="#7a838b", linewidth=0.9, linestyle=":")
series.axhline(0.35, color="#adb5bd", linewidth=0.8, linestyle="--")
series.axhline(0.65, color="#adb5bd", linewidth=0.8, linestyle="--")
series.set_ylim(0, 1)
series.set_xlabel("elapsed physical time (s)")
series.set_ylabel("published order parameter")
series.legend(frameon=False, ncol=2, loc="upper left")
series.text(
    0.995,
    0.03,
    "State labels use the published threshold rule with $k=0.35$",
    transform=series.transAxes,
    ha="right",
    va="bottom",
    fontsize=9,
    color="#65717c",
)

fig.suptitle(
    "Observed golden shiners move from a disordered regime towards sustained milling",
    fontsize=15,
)
fig.savefig(OUTPUT, transparent=True)
print(f"Wrote {OUTPUT}")
