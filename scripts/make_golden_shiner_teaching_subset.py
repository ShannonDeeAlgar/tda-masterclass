#!/usr/bin/env python3
"""Build the empirical dynamic-data teaching subset used by the Reader.

The source is the public Fish Schooling Data Subset:
https://doi.org/10.7267/zk51vq07c

The retained frames span a transition from relatively polarised motion towards
a sustained milling state.  This is a transparent course extraction, not a
reproduction of the analyses in the originating papers.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import urllib.request
from pathlib import Path

import numpy as np


SOURCE_URL = "https://ir.library.oregonstate.edu/downloads/9s161d47c"
SOURCE_SHA256 = "66ffab3090b86cc9993caba495b6c362ce4ca4d67084e531b9a58753dd65159e"
SOURCE_FPS = 30.0
FIRST_FRAME = 2701
LAST_FRAME = 3500
FRAME_STEP = 5
STATE_THRESHOLD = 0.35


def obtain_source(source: Path | None, download: Path) -> Path:
    if source is not None:
        return source
    download.parent.mkdir(parents=True, exist_ok=True)
    if not download.exists():
        urllib.request.urlretrieve(SOURCE_URL, download)
    digest = hashlib.sha256(download.read_bytes()).hexdigest()
    if digest != SOURCE_SHA256:
        raise ValueError(
            f"Source checksum is {digest}; expected {SOURCE_SHA256}."
        )
    return download


def order_parameters(frame: dict[str, list[float]]) -> tuple[float, float]:
    x = np.asarray(frame["px"], dtype=float)
    y = np.asarray(frame["py"], dtype=float)
    vx = np.asarray(frame["vx"], dtype=float)
    vy = np.asarray(frame["vy"], dtype=float)
    speed = np.hypot(vx, vy)
    moving = speed > np.finfo(float).eps
    ux = vx[moving] / speed[moving]
    uy = vy[moving] / speed[moving]
    polarisation = float(np.hypot(ux.mean(), uy.mean()))

    rx = x[moving] - x[moving].mean()
    ry = y[moving] - y[moving].mean()
    radius = np.hypot(rx, ry)
    away_from_centre = radius > np.finfo(float).eps
    rotation = float(
        abs(
            np.mean(
                (
                    rx[away_from_centre] * uy[away_from_centre]
                    - ry[away_from_centre] * ux[away_from_centre]
                )
                / radius[away_from_centre]
            )
        )
    )
    return polarisation, rotation


def state_label(polarisation: float, rotation: float) -> str:
    high = 1 - STATE_THRESHOLD
    if polarisation > high and rotation < STATE_THRESHOLD:
        return "polarised"
    if rotation > high and polarisation < STATE_THRESHOLD:
        return "milling"
    if polarisation < STATE_THRESHOLD and rotation < STATE_THRESHOLD:
        return "swarm"
    return "transition"


def build(source: Path, observations: Path, summary: Path) -> None:
    with source.open() as stream:
        frames = json.load(stream)

    selected = range(FIRST_FRAME, LAST_FRAME + 1, FRAME_STEP)
    observation_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []

    for teaching_frame, source_frame in enumerate(selected):
        frame = frames[str(source_frame)]
        polarisation, rotation = order_parameters(frame)
        label = state_label(polarisation, rotation)
        n_detected = len(frame["px"])
        summary_rows.append(
            {
                "teaching_frame": teaching_frame,
                "source_frame": source_frame,
                "time_s": (source_frame - FIRST_FRAME) / SOURCE_FPS,
                "n_detected": n_detected,
                "polarisation": polarisation,
                "rotation": rotation,
                "published_state_rule": label,
            }
        )
        for index in range(n_detected):
            observation_rows.append(
                {
                    "teaching_frame": teaching_frame,
                    "source_frame": source_frame,
                    "time_s": (source_frame - FIRST_FRAME) / SOURCE_FPS,
                    "track_id": frame["onfish"][index],
                    "x_px": frame["px"][index],
                    "y_px": frame["py"][index],
                    "vx_source": frame["vx"][index],
                    "vy_source": frame["vy"][index],
                }
            )

    observations.parent.mkdir(parents=True, exist_ok=True)
    with observations.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=observation_rows[0].keys())
        writer.writeheader()
        writer.writerows(observation_rows)
    with summary.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=summary_rows[0].keys())
        writer.writeheader()
        writer.writerows(summary_rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "source",
        nargs="?",
        type=Path,
        help="Downloaded schooling_frames.json; omit to fetch the public source",
    )
    parser.add_argument(
        "--download",
        type=Path,
        default=Path("/tmp/schooling_frames.json"),
        help="Cache location used only when source is omitted",
    )
    parser.add_argument(
        "--observations",
        type=Path,
        default=Path("data/golden_shiner_transition_observations.csv"),
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path("data/golden_shiner_transition_frames.csv"),
    )
    args = parser.parse_args()
    source = obtain_source(args.source, args.download)
    build(source, args.observations, args.summary)
    print(f"Wrote {args.observations}")
    print(f"Wrote {args.summary}")


if __name__ == "__main__":
    main()
