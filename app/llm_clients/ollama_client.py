"""Client for local Ollama Qwen‑2.5‑VL model.

This client sends a base64‑encoded image and optional JSON context to a
locally running Ollama server.  The server is expected to accept a POST
request at `/api/generate` with fields `model`, `prompt` and `images`.  The
response must contain a `response` field with the model's output.  If the
server is not available, the client falls back to returning the centre of
the image.
"""

from __future__ import annotations

import base64
import io
import json
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import requests


class OllamaClient:
    def __init__(self, url: str, model_name: str = "qwen2.5-vl"):
        self.url = url.rstrip("/")
        self.model_name = model_name

    def _encode_image(self, image: np.ndarray) -> str:
        """Encode an RGB numpy array as a PNG data URI."""
        success, buffer = cv2.imencode(".png", cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        if not success:
            raise RuntimeError("Failed to encode image")
        encoded = base64.b64encode(buffer.tobytes()).decode("ascii")
        return f"data:image/png;base64,{encoded}"

    def generate_action(self, prompt: str, image: np.ndarray, objects: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Send the observation to the model and return the parsed action.

        Args:
            prompt: The full prompt including system and user instructions.
            image: RGB image (224×224) to send.
            objects: Optional list of object dictionaries; included in the prompt.

        Returns:
            Parsed JSON action.  If the model fails, returns a centre click.
        """
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "images": [self._encode_image(image)],
        }
        try:
            resp = requests.post(self.url, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            text = data.get("response", "").strip()
            # Try to parse JSON; model may return markdown, so extract braces
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                json_str = text[start:end + 1]
                return json.loads(json_str)
        except Exception:
            pass
        # Fallback: centre click
        h, w = image.shape[:2]
        return {
            "click": [w // 2, h // 2],
            "modifiers": {"shift": False},
            "reason": "fallback centre click",
        }