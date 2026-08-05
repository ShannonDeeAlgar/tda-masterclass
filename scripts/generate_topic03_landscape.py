"""Render the double-well sublevel-set teaching figure."""

from pathlib import Path
import plistlib
import subprocess

# Matplotlib asks macOS system_profiler to enumerate every installed font when
# no font cache exists. That can stall in restricted or headless sessions. The
# figure uses Matplotlib's bundled DejaVu fonts, so skip only that enumeration.
_check_output = subprocess.check_output


def _check_output_without_system_fonts(command, *args, **kwargs):
    if command == ["system_profiler", "-xml", "SPFontsDataType"]:
        return plistlib.dumps([{"_items": []}])
    return _check_output(command, *args, **kwargs)


subprocess.check_output = _check_output_without_system_fonts

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgba


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "topic03-height-sublevel-3d.svg"

x = np.linspace(-1.75, 1.75, 42)
y = np.linspace(-1.25, 1.25, 32)
X, Y = np.meshgrid(x, y)
H = (X**2 - 1.0) ** 2 + 0.65 * Y**2
H = np.minimum(H, 3.0)

thresholds = (0.30, 1.00, 1.65)
titles = ("Below the saddle", "At the saddle", "Above the saddle")
summaries = ("two components", "the components meet", "one component")
fig = plt.figure(figsize=(12, 4.6), facecolor="none")
for index, (level, title, summary) in enumerate(
    zip(thresholds, titles, summaries), start=1
):
    ax = fig.add_subplot(1, 3, index, projection="3d", computed_zorder=False)
    ax.set_facecolor((1, 1, 1, 0))

    included = H <= level
    face_colours = np.empty(H.shape + (4,))
    face_colours[included] = to_rgba("#3f9290", 0.88)
    face_colours[~included] = to_rgba("#d7e1e0", 0.28)

    ax.plot_surface(
        X,
        Y,
        H,
        facecolors=face_colours,
        edgecolor="#446f70",
        linewidth=0.16,
        alpha=1.0,
        shade=False,
        antialiased=True,
        rstride=2,
        cstride=2,
        zorder=1,
    )

    # The translucent rectangle is the actual horizontal slicing plane.
    PX, PY = np.meshgrid([-1.72, 1.72], [-1.22, 1.22])
    PZ = np.full_like(PX, level)
    ax.plot_surface(PX, PY, PZ, color="#d29a52", alpha=0.18, shade=False, zorder=2)

    # Draw the intersection h(x,y)=a directly on the plane.
    ax.contour(
        X,
        Y,
        H,
        levels=[level],
        zdir="z",
        offset=level + 0.012,
        colors=["#9b5e22"],
        linewidths=2.2,
        zorder=4,
    )

    ax.set_title(f"{title}\n{summary}", fontsize=12, fontweight="semibold", pad=2)
    ax.set_xlim(-1.75, 1.75)
    ax.set_ylim(-1.25, 1.25)
    ax.set_zlim(0, 2.7)
    ax.set_box_aspect((1.5, 1.05, 1.0))
    ax.view_init(elev=29, azim=-58)
    ax.set_proj_type("ortho")
    ax.set_xlabel("x", labelpad=-7)
    ax.set_ylabel("y", labelpad=-7)
    ax.set_zlabel("h(x,y)", labelpad=-2)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([level])
    ax.set_zticklabels([rf"$a_{index}$"], fontsize=9)
    ax.grid(False)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.fill = False
        axis.pane.set_edgecolor((0.6, 0.65, 0.66, 0.35))

fig.subplots_adjust(left=0.01, right=0.99, bottom=0.02, top=0.96, wspace=0.0)
fig.savefig(OUTPUT, transparent=True, bbox_inches="tight", pad_inches=0.08)
plt.close(fig)
print(OUTPUT)
