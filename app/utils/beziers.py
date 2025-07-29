"""Bezier path generation for mouse movements."""

from __future__ import annotations

import random
from typing import Iterable, List, Tuple


def _cubic_bezier(t: float, p0: float, p1: float, p2: float, p3: float) -> float:
    """Compute a single dimension of a cubic Bezier curve."""
    return (
        (1 - t) ** 3 * p0
        + 3 * (1 - t) ** 2 * t * p1
        + 3 * (1 - t) * t ** 2 * p2
        + t ** 3 * p3
    )


def bezier_path(start: Tuple[int, int], end: Tuple[int, int], steps: int = 20) -> List[Tuple[int, int]]:
    """Generate a list of points along a cubic Bezier curve with jitter.

    The control points are selected near the start and end to create a
    plausible human‑like curve.  Random jitter is applied to the control
    points to avoid identical paths.

    Args:
        start: Current mouse position (absolute screen coords).
        end: Target position (absolute screen coords).
        steps: Number of points in the path.

    Returns:
        List of (x, y) tuples.
    """
    x0, y0 = start
    x3, y3 = end
    # Control points near the start and end with random offsets
    def rand_offset():
        return random.uniform(-30, 30)

    x1 = x0 + (x3 - x0) * 0.25 + rand_offset()
    y1 = y0 + (y3 - y0) * 0.25 + rand_offset()
    x2 = x0 + (x3 - x0) * 0.75 + rand_offset()
    y2 = y0 + (y3 - y0) * 0.75 + rand_offset()
    points: List[Tuple[int, int]] = []
    for i in range(steps):
        t = i / (steps - 1)
        x = _cubic_bezier(t, x0, x1, x2, x3)
        y = _cubic_bezier(t, y0, y1, y2, y3)
        points.append((int(x), int(y)))
    return points