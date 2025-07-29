#!/usr/bin/env bash
# Set up a Python virtual environment and launch Qwen‑Plays‑OSRS on Linux.

set -e
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip
# Install required packages
python -m pip install mss pyautogui opencv-python pyyaml pyzmq pydantic jsonschema pillow

echo "Starting Qwen‑Plays‑OSRS..."
python -m app.main --config "$1"