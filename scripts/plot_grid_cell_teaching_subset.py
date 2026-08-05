#!/usr/bin/env python3
"""Plot the empirical grid-cell teaching subset without implying a 2D torus."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


DATA = Path("data/grid_cell_torus_r_day1_module2_teaching.npz")
OUTPUT = Path("assets/grid-cell-teaching-subset.svg")

with np.load(DATA) as subset:
    x = subset["x"]
    y = subset["y"]
    time = subset["time"]
    scores = subset["pca_scores"]

order = np.argsort(time)
colours = plt.cm.viridis((time - time.min()) / (time.max() - time.min()))

fig = plt.figure(figsize=(10, 4.2), constrained_layout=True)
ax_position = fig.add_subplot(1, 2, 1)
ax_state = fig.add_subplot(1, 2, 2, projection="3d")

ax_position.plot(x[order], y[order], color="#b7c2cc", linewidth=0.35, alpha=0.45)
ax_position.scatter(x, y, c=colours, s=8, linewidths=0)
ax_position.set_title("Selected animal positions")
ax_position.set_xlabel("arena x")
ax_position.set_ylabel("arena y")
ax_position.set_aspect("equal")

ax_state.scatter(
    scores[:, 0],
    scores[:, 1],
    scores[:, 2],
    c=colours,
    s=8,
    linewidths=0,
    alpha=0.85,
)
ax_state.set_title("The same bins in the first three PCs")
ax_state.set_xlabel("PC1")
ax_state.set_ylabel("PC2")
ax_state.set_zlabel("PC3")
ax_state.view_init(elev=20, azim=38)

fig.suptitle(
    "Grid-cell teaching subset: behaviour and a low-dimensional projection",
    fontsize=14,
)
fig.savefig(OUTPUT, transparent=True)
print(f"Wrote {OUTPUT}")
