#!/usr/bin/env python3
"""Show what changes when temporal order is restored to the grid-cell subset."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


DATA = Path("data/grid_cell_torus_r_day1_module2_teaching.npz")
OUTPUT = Path("assets/grid-cell-dynamics-bridge.svg")

with np.load(DATA) as subset:
    x = subset["trajectory_x"]
    y = subset["trajectory_y"]
    scores = subset["trajectory_pca_scores"]
    time = subset["trajectory_time"]

elapsed = time - time[0]
colours = plt.cm.viridis(elapsed / elapsed[-1])

fig = plt.figure(figsize=(13, 4.25), constrained_layout=True)
arena = fig.add_subplot(1, 3, 1)
state = fig.add_subplot(1, 3, 2, projection="3d")
torus = fig.add_subplot(1, 3, 3, projection="3d")

arena.plot(x, y, color="#415a77", linewidth=1.4)
arena.scatter(x[::20], y[::20], c=colours[::20], s=16, linewidths=0)
arena.scatter(x[0], y[0], color="#a33d3d", marker="s", s=42, label="start")
arena.set_title("Observed 20 s passage")
arena.set_xlabel("arena x")
arena.set_ylabel("arena y")
arena.set_aspect("equal")
arena.legend(frameon=False, fontsize=8)

state.plot(scores[:, 0], scores[:, 1], scores[:, 2], color="#415a77", linewidth=1.2)
state.scatter(
    scores[::20, 0],
    scores[::20, 1],
    scores[::20, 2],
    c=colours[::20],
    s=16,
    linewidths=0,
)
state.set_title("Ordered neural-state trajectory")
state.set_xlabel("PC1")
state.set_ylabel("PC2")
state.set_zlabel("PC3")
state.view_init(elev=23, azim=42)

u = np.linspace(0, 2 * np.pi, 50)
v = np.linspace(0, 2 * np.pi, 25)
uu, vv = np.meshgrid(u, v)
major, minor = 1.5, 0.55
tx = (major + minor * np.cos(vv)) * np.cos(uu)
ty = (major + minor * np.cos(vv)) * np.sin(uu)
tz = minor * np.sin(vv)
torus.plot_surface(tx, ty, tz, color="#9fb9cf", alpha=0.28, linewidth=0)
path_u = np.linspace(0.35, 1.8 * np.pi, len(elapsed))
path_v = 0.8 + 1.4 * np.sin(np.linspace(0, 2.5 * np.pi, len(elapsed)))
px = (major + minor * np.cos(path_v)) * np.cos(path_u)
py = (major + minor * np.cos(path_v)) * np.sin(path_u)
pz = minor * np.sin(path_v)
torus.plot(px, py, pz, color="#a33d3d", linewidth=2)
torus.set_title("Dynamics on the inferred torus?")
torus.text2D(
    0.02,
    0.02,
    "Conceptual: requires decoded toroidal coordinates",
    transform=torus.transAxes,
    fontsize=8,
    color="#6a7480",
)
torus.set_axis_off()
torus.view_init(elev=24, azim=35)

fig.suptitle(
    "The same recordings support a static shape question and a dynamic path question",
    fontsize=14,
)
fig.savefig(OUTPUT, transparent=True)
print(f"Wrote {OUTPUT}")
