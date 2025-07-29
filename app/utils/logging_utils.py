"""Logging utilities for Qwen‑Plays‑OSRS.

This module sets up a run directory and configures Python's logging module to
write logs to both the console and a file.  Frames, prompts and actions are
also stored in this directory for later inspection.
"""

from __future__ import annotations

import datetime
import logging
import os
from typing import Optional


def prepare_run_dir(base_dir: Optional[str] = None) -> str:
    """Create a timestamped run directory.

    Args:
        base_dir: Optional base directory.  If None, uses 'runs' in the cwd.

    Returns:
        Path to the created directory.
    """
    root = base_dir or "runs"
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = os.path.join(root, ts)
    os.makedirs(path, exist_ok=True)
    return path


def setup_logging(log_dir: str) -> logging.Logger:
    """Configure a logger to write to a file and stdout.

    Args:
        log_dir: Directory where logs should be saved.

    Returns:
        A configured logger instance.
    """
    logger = logging.getLogger("qposrs")
    logger.setLevel(logging.INFO)
    # Clear existing handlers
    logger.handlers = []
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    # File handler
    fh = logging.FileHandler(os.path.join(log_dir, "run.log"), encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger