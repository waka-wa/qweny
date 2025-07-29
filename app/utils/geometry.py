"""Geometry helpers for points and rectangles."""

from __future__ import annotations

from typing import Tuple


def clamp_point(x: int, y: int, left: int, top: int, width: int, height: int) -> Tuple[int, int]:
    """Clamp a point to stay within a rectangle.

    Args:
        x: Absolute x coordinate.
        y: Absolute y coordinate.
        left: Left coordinate of the rectangle.
        top: Top coordinate of the rectangle.
        width: Width of the rectangle.
        height: Height of the rectangle.

    Returns:
        A tuple of clamped (x, y).
    """
    max_x = left + width - 1
    max_y = top + height - 1
    clamped_x = max(left, min(x, max_x))
    clamped_y = max(top, min(y, max_y))
    return clamped_x, clamped_y