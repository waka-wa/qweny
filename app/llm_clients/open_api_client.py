"""Generic HTTP client for remote Qwen‑2.5‑VL endpoints.

This client sends a JSON payload to an arbitrary HTTP endpoint.  The payload
contains the prompt, a base64‑encoded PNG image and optional JSON context.
The endpoint is expected to return a JSON object with a `response` field
containing a JSON string.  If anything goes wrong, the client produces a
centre click as a fallback.
"""

from __future__ import annotations

import base64
import json
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
import requests


class OpenAPIClient:
    def __init__(self, url: str, headers: Optional[Dict[str, str]] = None, model_name: Optional[str] = None):
        self.url = url
        self.headers = headers or {}
        self.model_name = model_name

    def _encode_image(self, image: np.ndarray) -> str:
        success, buffer = cv2.imencode(".png", cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        if not success:
            raise RuntimeError("Failed to encode image")
        encoded = base64.b64encode(buffer.tobytes()).decode("ascii")
        return f"data:image/png;base64,{encoded}"

    def generate_action(self, prompt: str, image: np.ndarray, objects: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        payload = {
            "prompt": prompt,
            "image": self._encode_image(image),
            "objects": objects or [],
        }
        if self.model_name:
            payload["model_name"] = self.model_name
        try:
            resp = requests.post(self.url, json=payload, headers=self.headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            text = data.get("response", "").strip()
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                json_str = text[start:end + 1]
                return json.loads(json_str)
        except Exception:
            pass
        # Fallback centre click
        h, w = image.shape[:2]
        return {
            "click": [w // 2, h // 2],
            "modifiers": {"shift": False},
            "reason": "fallback centre click",
        }