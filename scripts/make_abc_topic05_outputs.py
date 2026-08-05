"""Build the guiding A/B/C point set and its H1 teaching figure."""

from itertools import combinations
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_bipartite_matching

ROOT = Path(__file__).resolve().parents[1]
TITLE_STYLE = {
    "loc": "center",
    "fontsize": 12,
    "fontweight": "semibold",
    "color": "#294446",
    "pad": 10,
}


def panel_title(axis, text):
    """Apply the MasterClass subfigure-title convention."""
    axis.set_title(text, **TITLE_STYLE)


def abc_points():
    inner = np.array([
        [0, 0], [0, 22], [0, 44], [0, 66], [0, 88],
        [22, 0], [42, 5], [50, 23], [22, 44], [43, 44],
        [50, 65], [42, 85], [22, 88],
    ], dtype=float)
    outer = np.array([
        [350, 35, .82], [292, 105, .82], [408, 105, .82],
        [235, 183, .82], [465, 183, .82], [182, 263, .82],
        [518, 263, .82], [300, 225, .78], [400, 225, .78],
        [125, 340, .82], [575, 340, .82],
    ], dtype=float)
    return np.vstack([inner * scale + [x, y] for x, y, scale in outer])


def rips_h1(points, maximum=180.0):
    """Small transparent F2 reduction used only to generate the checked asset."""
    distances = np.linalg.norm(points[:, None] - points[None, :], axis=2)
    simplices = [((i,), 0.0, 0) for i in range(len(points))]
    for i, j in combinations(range(len(points)), 2):
        value = distances[i, j]
        if value <= maximum:
            simplices.append(((i, j), value, 1))
    for i, j, k in combinations(range(len(points)), 3):
        value = max(distances[i, j], distances[i, k], distances[j, k])
        if value <= maximum:
            simplices.append(((i, j, k), value, 2))
    simplices.sort(key=lambda item: (item[1], item[2], item[0]))
    index = {simplex: i for i, (simplex, _, _) in enumerate(simplices)}

    pivot_column, reduced, pairs, zero_columns = {}, {}, [], []
    for column, (simplex, _, dimension) in enumerate(simplices):
        boundary = (
            {index[face] for face in combinations(simplex, len(simplex) - 1)}
            if dimension else set()
        )
        while boundary and max(boundary) in pivot_column:
            boundary ^= reduced[pivot_column[max(boundary)]]
        if boundary:
            pivot = max(boundary)
            pivot_column[pivot] = column
            reduced[column] = boundary
            pairs.append((pivot, column))
        else:
            reduced[column] = set()
            zero_columns.append(column)

    intervals = []
    for birth, death in pairs:
        if simplices[birth][2] == 1:
            b, d = simplices[birth][1], simplices[death][1]
            if d - b > 1e-8:
                intervals.append((b, d))
    return np.array(sorted(intervals), dtype=float)


def category(birth, death):
    if birth > 50 and death - birth > 20:
        return "global A-scale loop"
    if 17 < birth < 20 and death - birth > 15:
        return "local B-scale loops"
    return "other short intervals"


def augmented_cost(first, second):
    n, m = len(first), len(second)
    cost = np.full((n + m, n + m), np.inf)
    cost[:n, :m] = np.max(np.abs(first[:, None, :] - second[None, :, :]), axis=2)
    for i, (birth, death) in enumerate(first):
        cost[i, m + i] = (death - birth) / 2
    for j, (birth, death) in enumerate(second):
        cost[n + j, j] = (death - birth) / 2
    cost[n:, m:] = 0
    return cost


def diagram_distances(first, second):
    cost = augmented_cost(first, second)
    finite_costs = np.unique(cost[np.isfinite(cost)])
    bottleneck = finite_costs[-1]
    for threshold in finite_costs:
        allowed = csr_matrix((cost <= threshold).astype(int))
        matching = maximum_bipartite_matching(allowed, perm_type="column")
        if np.all(matching >= 0):
            bottleneck = threshold
            break
    rows, columns = linear_sum_assignment(cost)
    wasserstein = cost[rows, columns].sum()
    return bottleneck, wasserstein


def betti_curve(diagram, grid):
    return np.array([np.sum((diagram[:, 0] <= value) & (value < diagram[:, 1])) for value in grid])


def landscape_levels(diagram, grid, levels=3):
    tents = np.array([
        np.maximum(0, np.minimum(grid - birth, death - grid))
        for birth, death in diagram
    ])
    return np.sort(tents, axis=0)[::-1][:levels]


def persistence_image(diagram, xgrid, ygrid, sigma=2.8):
    xmesh, ymesh = np.meshgrid(xgrid, ygrid)
    image = np.zeros_like(xmesh)
    for birth, death in diagram:
        persistence = death - birth
        image += persistence * np.exp(
            -((xmesh - birth) ** 2 + (ymesh - persistence) ** 2) / (2 * sigma ** 2)
        )
    return image


points = abc_points()
intervals = rips_h1(points)
np.savetxt(ROOT / "data/abc_points.csv", points, delimiter=",", header="x,y", comments="")
np.savetxt(
    ROOT / "data/abc_h1_intervals.csv", intervals, delimiter=",",
    header="birth,death", comments=""
)

colours = {
    "global A-scale loop": "#0d6670",
    "local B-scale loops": "#3f9699",
    "other short intervals": "#aeb9ba",
}
fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.2), gridspec_kw={"width_ratios": [1, 1.1, 1.1]})

axes[0].scatter(points[:, 0], -points[:, 1], s=9, color="#267f82", alpha=.9)
panel_title(axes[0], "The same 143 locations")
axes[0].set_aspect("equal")
axes[0].axis("off")

ordered = sorted(intervals, key=lambda pair: (category(*pair), pair[0], pair[1]))
for y, (birth, death) in enumerate(ordered):
    axes[1].plot([birth, death], [y, y], lw=2.4, color=colours[category(birth, death)])
panel_title(axes[1], "Barcode: one row per interval")
axes[1].set_xlabel("closeness scale")
axes[1].set_yticks([])
axes[1].spines[["left", "right", "top"]].set_visible(False)

limit = max(intervals[:, 1]) * 1.06
axes[2].plot([0, limit], [0, limit], ls="--", lw=1.2, color="#819092")
for label in ["other short intervals", "local B-scale loops", "global A-scale loop"]:
    mask = np.array([category(*pair) == label for pair in intervals])
    axes[2].scatter(intervals[mask, 0], intervals[mask, 1], s=34, color=colours[label], label=label)
axes[2].set(xlabel="birth", ylabel="death", xlim=(0, limit), ylim=(0, limit))
panel_title(axes[2], "Diagram: the same intervals as points")
axes[2].legend(frameon=False, fontsize=8, loc="upper left")
axes[2].spines[["right", "top"]].set_visible(False)

fig.suptitle("A/B/C Rips persistence in degree 1", x=.06, ha="left", fontsize=14, weight="bold")
fig.text(.06, .01, "Colour connects the same feature family across the barcode and diagram.", color="#556466")
fig.tight_layout(rect=(0, .04, 1, .93))
fig.savefig(ROOT / "assets/topic05-abc-barcode-diagram.svg", transparent=True, bbox_inches="tight")
fig.savefig(ROOT / "assets/topic05-abc-barcode-diagram.png", dpi=180, transparent=True, bbox_inches="tight")

rng = np.random.default_rng(5017)
perturbed_points = points + rng.normal(0, 1.5, points.shape)
perturbed = rips_h1(perturbed_points)
bottleneck, wasserstein = diagram_distances(intervals, perturbed)

grid = np.linspace(0, 95, 240)
curve = betti_curve(intervals, grid)
landscapes = landscape_levels(intervals, grid)
xgrid = np.linspace(0, 95, 80)
ygrid = np.linspace(0, 35, 60)
image = persistence_image(intervals, xgrid, ygrid)
lifetimes = intervals[:, 1] - intervals[:, 0]
probabilities = lifetimes / lifetimes.sum()
entropy = -np.sum(probabilities * np.log(probabilities))

fig = plt.figure(figsize=(14.2, 5.0))
layout = fig.add_gridspec(2, 4, width_ratios=[1.12, 1, 1, 1], wspace=.48, hspace=.42)
barcode_axis = fig.add_subplot(layout[0, 0])
diagram_axis = fig.add_subplot(layout[1, 0])
curve_axis = fig.add_subplot(layout[:, 1])
landscape_axis = fig.add_subplot(layout[:, 2])
image_axis = fig.add_subplot(layout[:, 3])

for y, (birth, death) in enumerate(ordered):
    barcode_axis.plot([birth, death], [y, y], lw=1.8, color=colours[category(birth, death)])
barcode_axis.set(xlabel="scale", yticks=[])
panel_title(barcode_axis, "Starting intervals: barcode")

limit = intervals[:, 1].max() * 1.05
diagram_axis.plot([0, limit], [0, limit], ls="--", lw=1, color="#819092")
for label in ["other short intervals", "local B-scale loops", "global A-scale loop"]:
    mask = np.array([category(*pair) == label for pair in intervals])
    diagram_axis.scatter(intervals[mask, 0], intervals[mask, 1], s=18, color=colours[label])
diagram_axis.set(xlabel="birth", ylabel="death", xlim=(0, limit), ylim=(0, limit))
panel_title(diagram_axis, "Starting intervals: diagram")

chosen_scale = 25
curve_axis.plot(grid, curve, color="#267f82", lw=2.4)
curve_axis.axvline(chosen_scale, color="#b36f2d", lw=1.1, ls="--")
curve_axis.scatter([chosen_scale], [betti_curve(intervals, np.array([chosen_scale]))[0]], color="#b36f2d", zorder=3)
curve_axis.set(xlabel="scale", ylabel=r"$\beta_1$")
panel_title(curve_axis, "Betti curve")
curve_axis.text(.02, .96, "count bars crossing each scale", transform=curve_axis.transAxes, va="top", color="#0d6670", fontsize=9)

all_tents = np.array([
    np.maximum(0, np.minimum(grid - birth, death - grid))
    for birth, death in intervals
])
for tent in all_tents:
    landscape_axis.plot(grid, tent, lw=.65, color="#b9c8c8", alpha=.45)
landscape_colours = ["#07566a", "#58aaa7", "#8bc8c3"]
for level, (values, colour) in enumerate(zip(landscapes, landscape_colours), start=1):
    landscape_axis.plot(grid, values, lw=2, color=colour, label=rf"$\lambda_{level}$")
landscape_axis.set(xlabel="scale", ylabel=r"landscape value $\lambda_k(t)$")
panel_title(landscape_axis, "Persistence landscape")
landscape_axis.text(.02, .96, "replace bars with tents; order heights", transform=landscape_axis.transAxes, va="top", color="#0d6670", fontsize=9)
landscape_axis.legend(frameon=False, fontsize=8, loc="upper right")

image_axis.imshow(
    image, origin="lower", extent=[xgrid.min(), xgrid.max(), ygrid.min(), ygrid.max()],
    aspect="auto", cmap="GnBu"
)
image_axis.scatter(intervals[:, 0], lifetimes, s=7, facecolor="none", edgecolor="#07566a", linewidth=.6)
image_axis.set(xlabel="birth", ylabel="persistence = death − birth")
panel_title(image_axis, "Persistence image")
image_axis.text(.02, .96, "use (birth, lifespan); smooth and bin", transform=image_axis.transAxes, va="top", color="#0d6670", fontsize=9)

for axis in [barcode_axis, diagram_axis, curve_axis, landscape_axis, image_axis]:
    axis.spines[["right", "top"]].set_visible(False)
fig.suptitle("Three transformations of the same A/B/C intervals", x=.055, ha="left", fontsize=14, weight="normal")
fig.tight_layout(rect=(0, .045, 1, .91))
fig.savefig(ROOT / "assets/topic05-abc-representations.svg", transparent=True, bbox_inches="tight")
fig.savefig(ROOT / "assets/topic05-abc-representations.png", dpi=180, transparent=True, bbox_inches="tight")

# Separate teaching figures allow each transformation to sit beside its definition.
fig, (source_axis, output_axis) = plt.subplots(1, 2, figsize=(7.4, 3.5), constrained_layout=True)
for y, (birth, death) in enumerate(ordered):
    source_axis.plot([birth, death], [y, y], lw=1.7, color=colours[category(birth, death)])
source_axis.axvline(chosen_scale, color="#b36f2d", lw=1.1, ls="--")
source_axis.set(xlabel="filtration scale", yticks=[])
panel_title(source_axis, "Barcode")
output_axis.plot(grid, curve, color="#267f82", lw=2.4)
output_axis.axvline(chosen_scale, color="#b36f2d", lw=1.1, ls="--")
output_axis.scatter([chosen_scale], [betti_curve(intervals, np.array([chosen_scale]))[0]], color="#b36f2d", zorder=3)
output_axis.set(xlabel="filtration scale", ylabel=r"$\beta_1(a)$")
panel_title(output_axis, "Betti curve")
for axis_item in (source_axis, output_axis):
    axis_item.spines[["right", "top"]].set_visible(False)
fig.savefig(ROOT / "assets/topic05-abc-betti-curve.svg", transparent=True, bbox_inches="tight")
fig.savefig(ROOT / "assets/topic05-abc-betti-curve.png", dpi=180, transparent=True, bbox_inches="tight")

fig, (source_axis, output_axis) = plt.subplots(1, 2, figsize=(7.4, 3.5), constrained_layout=True)
source_axis.plot([0, limit], [0, limit], ls="--", lw=1, color="#819092")
for label in ["other short intervals", "local B-scale loops", "global A-scale loop"]:
    mask = np.array([category(*pair) == label for pair in intervals])
    source_axis.scatter(intervals[mask, 0], intervals[mask, 1], s=22, color=colours[label])
source_axis.set(xlabel="birth", ylabel="death", xlim=(0, limit), ylim=(0, limit))
panel_title(source_axis, "Persistence diagram")
for level, (values, colour) in enumerate(zip(landscapes, landscape_colours), start=1):
    output_axis.plot(grid, values, lw=2, color=colour, label=rf"$\lambda_{level}$")
output_axis.set(xlabel=r"filtration scale $t$", ylabel=r"landscape value $\lambda_k(t)$")
panel_title(output_axis, "Persistence landscape")
output_axis.legend(frameon=False, fontsize=8)
for axis_item in (source_axis, output_axis):
    axis_item.spines[["right", "top"]].set_visible(False)
fig.savefig(ROOT / "assets/topic05-abc-landscape.svg", transparent=True, bbox_inches="tight")
fig.savefig(ROOT / "assets/topic05-abc-landscape.png", dpi=180, transparent=True, bbox_inches="tight")

fig, (source_axis, output_axis) = plt.subplots(1, 2, figsize=(7.4, 3.5), constrained_layout=True)
source_axis.plot([0, limit], [0, limit], ls="--", lw=1, color="#819092")
for label in ["other short intervals", "local B-scale loops", "global A-scale loop"]:
    mask = np.array([category(*pair) == label for pair in intervals])
    source_axis.scatter(intervals[mask, 0], intervals[mask, 1], s=22, color=colours[label])
source_axis.set(xlabel="birth", ylabel="death", xlim=(0, limit), ylim=(0, limit))
panel_title(source_axis, "Persistence diagram")
output_axis.imshow(
    image, origin="lower", extent=[xgrid.min(), xgrid.max(), ygrid.min(), ygrid.max()],
    aspect="auto", cmap="GnBu"
)
output_axis.scatter(intervals[:, 0], lifetimes, s=7, facecolor="none", edgecolor="#07566a", linewidth=.6)
output_axis.set(xlabel="birth", ylabel="persistence = death − birth")
panel_title(output_axis, "Persistence image")
source_axis.spines[["right", "top"]].set_visible(False)
fig.savefig(ROOT / "assets/topic05-abc-persistence-image.svg", transparent=True, bbox_inches="tight")
fig.savefig(ROOT / "assets/topic05-abc-persistence-image.png", dpi=180, transparent=True, bbox_inches="tight")

fig, (data_axis, axis) = plt.subplots(1, 2, figsize=(12.4, 5.2), gridspec_kw={"width_ratios": [1, 1.15]})
data_axis.scatter(points[:, 0], -points[:, 1], s=16, color="#9aabad", alpha=.65, label="original")
data_axis.scatter(perturbed_points[:, 0], -perturbed_points[:, 1], s=23, facecolor="none", edgecolor="#c46c43", linewidth=.8, label="perturbed")
data_axis.set_aspect("equal")
panel_title(data_axis, "A small coordinate perturbation")
data_axis.legend(frameon=False, loc="upper right")
data_axis.axis("off")
comparison_limit = max(intervals[:, 1].max(), perturbed[:, 1].max()) * 1.05
axis.plot([0, comparison_limit], [0, comparison_limit], ls="--", lw=1, color="#819092")
matching_cost = augmented_cost(intervals, perturbed)
rows, columns = linear_sum_assignment(matching_cost)
for row, column in zip(rows, columns):
    if row < len(intervals) and column < len(perturbed):
        first, second = intervals[row], perturbed[column]
    elif row < len(intervals):
        first = intervals[row]
        midpoint = first.mean()
        second = np.array([midpoint, midpoint])
    elif column < len(perturbed):
        second = perturbed[column]
        midpoint = second.mean()
        first = np.array([midpoint, midpoint])
    else:
        continue
    axis.plot([first[0], second[0]], [first[1], second[1]], color="#b7c5c5", lw=.8, zorder=1)
axis.scatter(intervals[:, 0], intervals[:, 1], s=34, color="#07566a", label="original", zorder=3)
axis.scatter(perturbed[:, 0], perturbed[:, 1], s=34, facecolor="none", edgecolor="#c46c43", linewidth=1.2, label="perturbed", zorder=3)
axis.set(xlabel="birth", ylabel="death", xlim=(0, comparison_limit), ylim=(0, comparison_limit))
panel_title(axis, "The resulting diagrams")
axis.legend(frameon=False)
axis.spines[["right", "top"]].set_visible(False)
fig.text(.53, .015, f"bottleneck distance = {bottleneck:.2f}   ·   1-Wasserstein distance = {wasserstein:.2f}", color="#556466")
fig.tight_layout(rect=(0, .05, 1, 1))
fig.savefig(ROOT / "assets/topic05-abc-perturbation.svg", transparent=True, bbox_inches="tight")
fig.savefig(ROOT / "assets/topic05-abc-perturbation.png", dpi=180, transparent=True, bbox_inches="tight")
