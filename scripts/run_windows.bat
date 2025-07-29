@echo off
REM Set up a Python virtual environment and launch Qwen‑Plays‑OSRS on Windows.

if not exist .venv (
  python -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip
REM Install required packages
python -m pip install mss pyautogui opencv-python pyyaml pyzmq pydantic jsonschema pillow

echo Starting Qwen‑Plays‑OSRS...
python -m app.main --config %1