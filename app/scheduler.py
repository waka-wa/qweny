"""Tick scheduler for pacing actions.

This module defines a simple scheduler that enforces a minimum time interval
between successive actions.  It is used to mimic game ticks (roughly
0.6 seconds per tick in Old School RuneScape) and avoid rapid double‑clicks.
"""

from __future__ import annotations

import time


class TickScheduler:
    """Scheduler to enforce minimum intervals between actions."""

    def __init__(self, min_interval: float = 0.6):
        self.min_interval = float(min_interval)
        self.last_time: float = 0.0

    def wait_for_next_tick(self) -> None:
        """Wait until the minimum interval has elapsed since the last action."""
        now = time.time()
        elapsed = now - self.last_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_time = time.time()

    def reset(self) -> None:
        """Reset the scheduler timer."""
        self.last_time = 0.0