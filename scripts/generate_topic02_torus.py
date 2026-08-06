"""Insert a parametrically generated torus and its two fundamental cycles."""

from __future__ import annotations

import colorsys
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "assets/topic02-classic-homology.svg"
START = "  <!-- TORUS PARAMETRIC START -->"
END = "  <!-- TORUS PARAMETRIC END -->"

R_MAJOR = 1.55
R_MINOR = 0.56
AZIMUTH = math.radians(-58)
ELEVATION = math.radians(27)
CENTER = (970.0, 164.0)
SCALE = 49.0

CAMERA = (
    math.cos(ELEVATION) * math.cos(AZIMUTH),
    math.cos(ELEVATION) * math.sin(AZIMUTH),
    math.sin(ELEVATION),
)
RIGHT = (-math.sin(AZIMUTH), math.cos(AZIMUTH), 0.0)
UP = (
    -math.sin(ELEVATION) * math.cos(AZIMUTH),
    -math.sin(ELEVATION) * math.sin(AZIMUTH),
    math.cos(ELEVATION),
)


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def point(u, v):
    radius = R_MAJOR + R_MINOR * math.cos(v)
    return radius * math.cos(u), radius * math.sin(u), R_MINOR * math.sin(v)


def normal(u, v):
    return math.cos(v) * math.cos(u), math.cos(v) * math.sin(u), math.sin(v)


def project(p):
    return (
        CENTER[0] + SCALE * dot(p, RIGHT),
        CENTER[1] - SCALE * dot(p, UP),
        dot(p, CAMERA),
    )


def colour(light):
    """Muted teal shading with enough contrast to reveal the surface."""
    light = max(0.0, min(1.0, light))
    dark = (0x78, 0xB8, 0xB7)
    pale = (0xDE, 0xF0, 0xEE)
    rgb = tuple(round(d + light * (p - d)) for d, p in zip(dark, pale))
    return "#" + "".join(f"{value:02x}" for value in rgb)


def path(points):
    coords = [project(item) for item in points]
    return "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y, _ in coords)


def surface_polygons():
    nu, nv = 42, 18
    polygons = []
    light_direction = (0.2, -0.35, 0.92)
    length = math.sqrt(dot(light_direction, light_direction))
    light_direction = tuple(value / length for value in light_direction)

    for i in range(nu):
        u0 = 2 * math.pi * i / nu
        u1 = 2 * math.pi * (i + 1) / nu
        for j in range(nv):
            v0 = 2 * math.pi * j / nv
            v1 = 2 * math.pi * (j + 1) / nv
            corners = [point(u0, v0), point(u1, v0), point(u1, v1), point(u0, v1)]
            projected = [project(item) for item in corners]
            depth = sum(item[2] for item in projected) / 4
            n = normal((u0 + u1) / 2, (v0 + v1) / 2)
            illumination = 0.48 + 0.42 * max(-0.15, dot(n, light_direction))
            data = " ".join(f"{x:.2f},{y:.2f}" for x, y, _ in projected)
            polygons.append((depth, f'  <polygon points="{data}" fill="{colour(illumination)}"/>'))

    return [line for _, line in sorted(polygons)]


def mesh_curves():
    lines = []
    for i in range(0, 42, 6):
        u = 2 * math.pi * i / 42
        samples = [point(u, 2 * math.pi * j / 90) for j in range(91)]
        lines.append(f'  <path d="{path(samples)}" class="torus-mesh"/>')
    for j in range(0, 18, 3):
        v = 2 * math.pi * j / 18
        samples = [point(2 * math.pi * i / 150, v) for i in range(151)]
        lines.append(f'  <path d="{path(samples)}" class="torus-mesh"/>')
    return lines


def split_visibility(samples):
    runs = []
    current = []
    current_visible = None
    for u, v in samples:
        visible = dot(normal(u, v), CAMERA) >= 0
        p = point(u, v)
        if current_visible is None or visible == current_visible:
            current.append(p)
        else:
            current.append(p)
            runs.append((current_visible, current))
            current = [current[-1], p]
        current_visible = visible
    if current:
        runs.append((current_visible, current))
    return runs


def cycles():
    lines = []

    # Longitude: a true coordinate circle u -> T(u, pi/2) on the top of the tube.
    longitude = [point(2 * math.pi * i / 220, math.pi / 2) for i in range(221)]
    lines.append(f'  <path d="{path(longitude)}" class="loop-a"/>')

    # Meridian: a true coordinate circle v -> T(u0, v) around one tube section.
    u0 = AZIMUTH + math.radians(54)
    meridian = [(u0, 2 * math.pi * i / 220) for i in range(221)]
    for visible, run in split_visibility(meridian):
        css = "loop-b" if visible else "loop-b-hidden"
        lines.append(f'  <path d="{path(run)}" class="{css}"/>')
    return lines


def build_group():
    return "\n".join([
        START,
        '  <g aria-label="Parametric torus with longitude and meridian cycles">',
        *surface_polygons(),
        *mesh_curves(),
        *cycles(),
        "  </g>",
        END,
    ])


def main():
    text = ASSET.read_text()
    start = text.index(START)
    end = text.index(END, start) + len(END)
    ASSET.write_text(text[:start] + build_group() + text[end:])


if __name__ == "__main__":
    main()
