"""Tests for the clamp_point helper."""

from app.utils.geometry import clamp_point


def test_clamp_inside():
    x, y = clamp_point(150, 200, left=100, top=100, width=50, height=50)
    assert (x, y) == (150, 200)


def test_clamp_left_top():
    x, y = clamp_point(50, 50, left=100, top=100, width=200, height=200)
    assert (x, y) == (100, 100)


def test_clamp_right_bottom():
    x, y = clamp_point(400, 500, left=100, top=100, width=200, height=200)
    # width and height define max coordinate at left+width-1
    assert (x, y) == (100 + 200 - 1, 100 + 200 - 1)