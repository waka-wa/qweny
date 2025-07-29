"""LLM client interfaces.

This package provides abstract and concrete clients for sending
observations (images and optional JSON) to a Qwen‑2.5‑VL backend and
receiving click predictions.  Two implementations are provided: a client
for **Ollama** and a generic HTTP client for any API.  If no backend is
available, a dummy client can produce centre clicks for demo purposes.
"""

from .ollama_client import OllamaClient
from .open_api_client import OpenAPIClient

__all__ = ["OllamaClient", "OpenAPIClient"]