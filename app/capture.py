"""Screen capture utilities.

This module wraps the `mss` library to capture a rectangular region of the
desktop at a specified frame rate.  Captured frames can be downscaled to
224×224 pixels and optionally masked to hide the chatbox.  The capture
functions return images in RGB numpy array format.
"""

from __future__ import annotations

import time
from typing import Optional, Tuple

import mss
import numpy as np
import cv2


class ScreenCapturer:
    """Capture a region of the screen at a given frame rate."""

    def __init__(self, rect: dict, fps: float = 2.0, mask_chat: bool = True):
        """Create a new capturer.

        Args:
            rect: A dictionary with `left`, `top`, `width`, `height` keys.
            fps: Target frames per second.
            mask_chat: If true, mask out the lower chat area to reduce noise.
        """
        self.rect = rect
        self.fps = fps
        self.mask_chat = mask_chat
        self.sct = mss.mss()
        self._last_time: float = 0.0

    def grab(self) -> np.ndarray:
        """Grab the current frame.

        Returns:
            A numpy array in RGB format with shape (h, w, 3).
        """
        monitor = {
            "left": self.rect["left"],
            "top": self.rect["top"],
            "width": self.rect["width"],
            "height": self.rect["height"],
        }
        frame = self.sct.grab(monitor)
        img = np.array(frame)
        # mss returns BGRA; convert to RGB and drop alpha
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
        if self.mask_chat:
            # For OSRS, the chatbox occupies roughly the bottom 20% of the window.
            h = img.shape[0]
            chat_y = int(h * 0.8)
            img[chat_y:, :] = 0
        return img

    def grab_resized(self, size: Tuple[int, int] = (224, 224)) -> np.ndarray:
        """Grab and resize the frame to the desired size.

        Args:
            size: Target (width, height).

        Returns:
            Resized image as a numpy array in RGB format.
        """
        img = self.grab()
        resized = cv2.resize(img, size, interpolation=cv2.INTER_AREA)
        return resized

    def wait(self) -> None:
        """Sleep to honour the frame rate."""
        if self.fps <= 0:
            return
        now = time.time()
        period = 1.0 / self.fps
        dt = now - self._last_time
        if dt < period:
            time.sleep(period - dt)
        self._last_time = time.time()