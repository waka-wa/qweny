"""Simple overlay drawing for debugging.

This module provides helpers for annotating frames with click markers and
bounding boxes.  It depends on OpenCV for drawing shapes and text.  These
functions should only be used in debug or demo mode; overlays are not
rendered during live operation to minimise overhead.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import cv2
import numpy as np


def draw_click(frame: np.ndarray, click: Tuple[int, int], color: Tuple[int, int, int] = (255, 0, 0)) -> np.ndarray:
    """Draw a small circle at the click location.

    Args:
        frame: RGB image.
        click: (x, y) relative coordinates within the frame.
        color: Colour as (R, G, B).

    Returns:
        Annotated image (copy of frame).
    """
    out = frame.copy()
    x, y = int(click[0]), int(click[1])
    cv2.circle(out, (x, y), radius=3, color=tuple(int(c) for c in color), thickness=-1)
    return out


def draw_objects(frame: np.ndarray, objects: List[dict]) -> np.ndarray:
    """Draw bounding boxes for detected objects.

    Args:
        frame: RGB image.
        objects: List of objects with keys `bbox` (x1,y1,x2,y2) and `name`.

    Returns:
        Annotated image.
    """
    out = frame.copy()
    for obj in objects:
        bbox = obj.get("bbox")
        if not bbox:
            continue
        x1, y1, x2, y2 = bbox
        cv2.rectangle(out, (x1, y1), (x2, y2), color=(0, 255, 0), thickness=1)
        name = obj.get("name", "")
        if name:
            cv2.putText(out, name, (x1, max(y1 - 5, 0)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1, cv2.LINE_AA)
    return out