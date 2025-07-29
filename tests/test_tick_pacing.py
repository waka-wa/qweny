"""Tests for the TickScheduler."""

import time
from app.scheduler import TickScheduler


def test_tick_pacing():
    scheduler = TickScheduler(min_interval=0.4)
    start = time.time()
    scheduler.wait_for_next_tick()  # first call should not sleep (last_time=0)
    mid = time.time()
    # Immediately call again; should sleep ~0.4 seconds
    scheduler.wait_for_next_tick()
    end = time.time()
    # The interval between mid and end should be >= 0.39s
    assert (end - mid) >= 0.39