#!/usr/bin/env python3
"""Build the small empirical grid-cell subset used by the Reader.

The source is the public archive accompanying Gardner et al. (2022):
https://doi.org/10.6084/m9.figshare.16764508.v6

This is deliberately a transparent teaching transformation, not a reproduction
of the authors' complete denoising and persistent-cohomology pipeline.
"""

from __future__ import annotations

import argparse
import tempfile
import zipfile
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter1d


SOURCE_NAME = "rat_r_day1_grid_modules_1_2_3.npz"
SESSION_START = 7457.0
SESSION_END = 16045.0
INVALID_INTERVAL = (14778.0, 14890.0)
BIN_WIDTH = 0.05
SPEED_THRESHOLD = 2.5
ACTIVE_CANDIDATES = 15_000
N_POINTS = 1_200
PCA_DIMENSION = 6
DYNAMIC_SECONDS = 20
SEED = 20220728


def source_npz(path: Path, temporary: Path) -> Path:
    if path.suffix == ".npz":
        return path
    if not zipfile.is_zipfile(path):
        raise ValueError("Source must be the Figshare ZIP archive or its R day 1 NPZ file.")
    with zipfile.ZipFile(path) as archive:
        member = next(
            name for name in archive.namelist() if name.endswith("/" + SOURCE_NAME)
        )
        archive.extract(member, temporary)
    return temporary / member


def bin_and_smooth(spike_times: dict[int, np.ndarray], edges: np.ndarray) -> np.ndarray:
    rates = np.empty((len(edges) - 1, len(spike_times)), dtype=np.float32)
    for column, cell in enumerate(sorted(spike_times)):
        counts, _ = np.histogram(spike_times[cell], bins=edges)
        rates[:, column] = gaussian_filter1d(
            counts.astype(np.float32) / BIN_WIDTH,
            sigma=BIN_WIDTH / BIN_WIDTH,
            mode="constant",
        )
    return rates


def position_and_speed(
    source_time: np.ndarray,
    source_x: np.ndarray,
    source_y: np.ndarray,
    centres: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x = np.interp(centres, source_time, source_x)
    y = np.interp(centres, source_time, source_y)
    # The supplied coordinates are in metres; the authors' 2.5 threshold is cm/s.
    speed = 100 * np.hypot(np.gradient(x, BIN_WIDTH), np.gradient(y, BIN_WIDTH))
    return x.astype(np.float32), y.astype(np.float32), speed.astype(np.float32)


def standardised_pca(
    values: np.ndarray, dimensions: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    mean = values.mean(axis=0)
    scale = values.std(axis=0)
    scale[scale == 0] = 1
    standardised = (values - mean) / scale
    _, _, vt = np.linalg.svd(standardised, full_matrices=False)
    scores = standardised @ vt[:dimensions].T
    return (
        scores.astype(np.float32),
        vt[:dimensions].astype(np.float32),
        mean.astype(np.float32),
        scale.astype(np.float32),
    )


def dynamic_window(
    valid: np.ndarray, activity: np.ndarray, length: int
) -> np.ndarray:
    """Choose one contiguous, active passage while retaining every time bin."""
    moving_count = np.convolve(valid.astype(np.int16), np.ones(length), mode="valid")
    activity_sum = np.convolve(activity, np.ones(length), mode="valid")
    permitted = np.ones(len(moving_count), dtype=bool)
    invalid_start = int((INVALID_INTERVAL[0] - SESSION_START) / BIN_WIDTH)
    invalid_end = int((INVALID_INTERVAL[1] - SESSION_START) / BIN_WIDTH)
    permitted[max(0, invalid_start - length + 1) : invalid_end] = False
    score = moving_count.astype(np.float64) * (activity_sum.max() + 1) + activity_sum
    score[~permitted] = -np.inf
    start = int(np.argmax(score))
    return np.arange(start, start + length)


def cosine_farthest_points(values: np.ndarray, count: int, seed: int) -> np.ndarray:
    """Select a spread of points without claiming to reproduce the paper's sampler."""
    norms = np.linalg.norm(values, axis=1, keepdims=True)
    unit = values / np.maximum(norms, np.finfo(values.dtype).eps)
    rng = np.random.default_rng(seed)
    selected = np.empty(count, dtype=np.int32)
    selected[0] = rng.integers(len(values))
    best_distance = np.full(len(values), np.inf, dtype=np.float32)
    for i in range(1, count):
        distance = 1.0 - unit @ unit[selected[i - 1]]
        best_distance = np.minimum(best_distance, distance)
        best_distance[selected[:i]] = -1
        selected[i] = int(np.argmax(best_distance))
    return selected


def build(source: Path, output: Path) -> None:
    with tempfile.TemporaryDirectory() as directory:
        npz_path = source_npz(source, Path(directory))
        with np.load(npz_path, allow_pickle=True) as recording:
            spike_times = recording["spikes_mod2"].item()
            source_time = recording["t"]
            source_x = recording["x"]
            source_y = recording["y"]

        edges = np.arange(SESSION_START, SESSION_END + BIN_WIDTH, BIN_WIDTH)
        centres = (edges[:-1] + edges[1:]) / 2
        rates = bin_and_smooth(spike_times, edges)
        x, y, speed = position_and_speed(source_time, source_x, source_y, centres)

        valid = (
            (speed > SPEED_THRESHOLD)
            & ~((centres >= INVALID_INTERVAL[0]) & (centres < INVALID_INTERVAL[1]))
        )
        valid_indices = np.flatnonzero(valid)
        activity = rates[valid_indices].sum(axis=1)
        candidate_order = np.argsort(activity, kind="stable")[-ACTIVE_CANDIDATES:]
        candidate_indices = valid_indices[np.sort(candidate_order)]

        pca_scores, pca_components, pca_mean, pca_scale = standardised_pca(
            rates[candidate_indices], PCA_DIMENSION
        )
        chosen = cosine_farthest_points(pca_scores, N_POINTS, SEED)
        indices = candidate_indices[chosen]
        trajectory_indices = dynamic_window(
            valid, rates.sum(axis=1), int(DYNAMIC_SECONDS / BIN_WIDTH)
        )
        trajectory_scores = (
            (rates[trajectory_indices] - pca_mean) / pca_scale
        ) @ pca_components.T

        output.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            output,
            population_vectors=rates[indices],
            pca_scores=pca_scores[chosen],
            pca_components=pca_components,
            pca_mean=pca_mean,
            pca_scale=pca_scale,
            time=centres[indices].astype(np.float32),
            x=x[indices],
            y=y[indices],
            speed=speed[indices],
            trajectory_population_vectors=rates[trajectory_indices],
            trajectory_pca_scores=trajectory_scores.astype(np.float32),
            trajectory_time=centres[trajectory_indices].astype(np.float32),
            trajectory_x=x[trajectory_indices],
            trajectory_y=y[trajectory_indices],
            trajectory_speed=speed[trajectory_indices],
            trajectory_moving_mask=valid[trajectory_indices],
            source_cell_ids=np.asarray(sorted(spike_times), dtype=np.int16),
            source_doi=np.array("10.6084/m9.figshare.16764508.v6"),
            source_article_doi=np.array("10.1038/s41586-021-04268-7"),
            source_licence=np.array("CC0"),
            processing_note=np.array(
                "Teaching subset: 50 ms bins; Gaussian smoothing sigma 50 ms; "
                "speed > 2.5; 15,000 highest-activity candidates; standardise; "
                "PCA to 6 dimensions; cosine farthest-point selection to 1,200. "
                "A separate contiguous 20 s passage retains temporal order. "
                "This is not the authors' complete published pipeline."
            ),
            bin_width=np.float32(BIN_WIDTH),
            speed_threshold=np.float32(SPEED_THRESHOLD),
            random_seed=np.int32(SEED),
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "source",
        type=Path,
        help="Figshare ZIP archive or extracted rat R day 1 NPZ file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/grid_cell_torus_r_day1_module2_teaching.npz"),
    )
    args = parser.parse_args()
    build(args.source, args.output)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
