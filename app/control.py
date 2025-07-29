"""Mouse control utilities.

This module wraps PyAutoGUI to move the mouse and click in a human‑like
fashion.  It clamps coordinates within a configured window rectangle and
computes simple Bezier curves with jitter to avoid straight‑line movements.
"""

from __future__ import annotations

import random
import time
from typing import Iterable, Tuple

import pyautogui

from .utils.geometry import clamp_point
from .utils.beziers import bezier_path


def move_and_click(target: Tuple[int, int], window_rect: dict, duration: float = 0.1) -> None:
    """Move the mouse to the target and perform a click.

    Args:
        target: (x, y) coordinates relative to the OSRS window.
        window_rect: Dictionary with absolute screen position and size.
        duration: Total time for the movement.
    """
    # Convert target relative coordinates into absolute screen coordinates
    abs_x = window_rect["left"] + target[0]
    abs_y = window_rect["top"] + target[1]
    # Clamp to ensure we never click outside
    abs_x, abs_y = clamp_point(abs_x, abs_y,
                               window_rect["left"], window_rect["top"],
                               window_rect["width"], window_rect["height"])
    # Generate a path with jitter
    current_pos = pyautogui.position()
    path: Iterable[Tuple[int, int]] = bezier_path(current_pos, (abs_x, abs_y), steps=15)
    start_time = time.time()
    for i, (px, py) in enumerate(path):
        # Interpolate time to maintain constant overall duration
        now = time.time()
        t_elapsed = now - start_time
        t_target = duration * (i / max(len(path) - 1, 1))
        if t_target > t_elapsed:
            time.sleep(t_target - t_elapsed)
        pyautogui.moveTo(px, py)
    pyautogui.click()