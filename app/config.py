"""Configuration loader for Qwen‑Plays‑OSRS.

This module defines dataclasses for the application configuration and helper
functions to load YAML files.  Keeping configuration in YAML allows users to
customise their window rectangle, frame rate and model backend without
modifying code.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import yaml


@dataclass
class ModelConfig:
    """Configuration for the LLM backend."""

    backend: str = "ollama"
    url: str = "http://localhost:11434/api/generate"
    model_name: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class WindowRect:
    """Represent a rectangular region in absolute screen coordinates."""

    left: int
    top: int
    width: int
    height: int

    def as_dict(self) -> Dict[str, int]:
        return dataclasses.asdict(self)


@dataclass
class AppConfig:
    """Top‑level application configuration."""

    window: WindowRect
    fps: float = 2.0
    model: ModelConfig = field(default_factory=ModelConfig)
    plugin_enabled: bool = False
    rag_enabled: bool = False
    log_dir: Optional[str] = None


def _parse_window(data: Dict[str, Any]) -> WindowRect:
    try:
        return WindowRect(
            left=int(data.get("left", 0)),
            top=int(data.get("top", 0)),
            width=int(data.get("width", 765)),
            height=int(data.get("height", 503)),
        )
    except Exception as exc:
        raise ValueError(f"Invalid window configuration: {data}") from exc


def load_config(path: str) -> AppConfig:
    """Load a YAML configuration file and return an AppConfig.

    The YAML file must contain at least the `window` section; other fields are
    optional.  Unknown keys are ignored.

    Args:
        path: Path to a YAML file.

    Returns:
        AppConfig: The parsed configuration.
    """
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}

    window = _parse_window(data.get("window", {}))

    model_data = data.get("model", {})
    model = ModelConfig(
        backend=model_data.get("backend", "ollama"),
        url=model_data.get("url", "http://localhost:11434/api/generate"),
        model_name=model_data.get("model_name"),
        headers=model_data.get("headers", {}) or {},
    )

    return AppConfig(
        window=window,
        fps=float(data.get("fps", 2.0)),
        model=model,
        plugin_enabled=bool(data.get("plugin_enabled", False)),
        rag_enabled=bool(data.get("rag_enabled", False)),
        log_dir=data.get("log_dir"),
    )