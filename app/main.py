"""Main entry point for Qwen‑Plays‑OSRS.

This script can be run as a standalone program to either launch the Tkinter
GUI, run the offline replay harness or capture the screen live.  It ties
together configuration loading, screen capture, LLM inference and mouse
control.  Use `python -m qwen_plays_osrs.app.main --help` for options.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from pathlib import Path
from typing import List, Optional

import numpy as np
import tkinter as tk
import cv2
from tkinter import messagebox

from .config import load_config
from .capture import ScreenCapturer
from .scheduler import TickScheduler
from .overlay import draw_click, draw_objects
from .utils.logging_utils import prepare_run_dir, setup_logging
from .llm_clients import OllamaClient, OpenAPIClient
from .control import move_and_click


def build_system_prompt() -> str:
    """Load the system prompt from prompts/system_qwen.md."""
    prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "system_qwen.md"
    with open(prompt_path, "r", encoding="utf-8") as fh:
        return fh.read().strip()


def select_client(config) -> object:
    """Create an LLM client based on the model backend."""
    backend = config.model.backend.lower()
    if backend == "ollama":
        return OllamaClient(url=config.model.url, model_name=config.model.model_name or "qwen2.5-vl")
    elif backend == "open_api":
        return OpenAPIClient(url=config.model.url, headers=config.model.headers, model_name=config.model.model_name)
    else:
        # fallback dummy client
        from typing import Any, Dict
        class DummyClient:
            def generate_action(self, prompt: str, image: np.ndarray, objects: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
                h, w = image.shape[:2]
                return {"click": [w // 2, h // 2], "modifiers": {"shift": False}, "reason": "dummy"}
        return DummyClient()


def run_demo(config_path: str, limit: int = 10) -> None:
    """Run the offline replay harness using prerecorded frames."""
    config = load_config(config_path)
    run_dir = prepare_run_dir(config.log_dir)
    logger = setup_logging(run_dir)
    logger.info("Starting demo harness…")
    capturer = ScreenCapturer(config.window.as_dict(), fps=config.fps)
    client = select_client(config)
    system_prompt = build_system_prompt()
    demo_dir = Path(__file__).resolve().parent.parent / "demo_frames"
    frames = sorted([p for p in demo_dir.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg"}])
    if not frames:
        logger.error("No demo frames found in demo_frames/ directory.")
        return
    total = min(limit, len(frames))
    for idx, frame_path in enumerate(frames[:total]):
        img = cv2.imread(str(frame_path))
        if img is None:
            continue
        # Convert BGR to RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(img_rgb, (224, 224))
        action = client.generate_action(system_prompt, resized, objects=None)
        logger.info(f"Frame {idx+1}/{total}: action {action}")
        # Draw overlay and save for inspection
        click = tuple(action.get("click", [112, 112]))
        annotated = draw_click(resized, click)
        out_path = Path(run_dir) / f"demo_{idx+1:04d}.png"
        cv2.imwrite(str(out_path), cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR))
        # Sleep to simulate pacing
        time.sleep(1.0 / config.fps)
    logger.info("Demo completed.")


def run_live(config_path: str) -> None:
    """Run the live capture loop."""
    config = load_config(config_path)
    run_dir = prepare_run_dir(config.log_dir)
    logger = setup_logging(run_dir)
    logger.info("Starting live capture… press Ctrl+C to exit.")
    capturer = ScreenCapturer(config.window.as_dict(), fps=config.fps)
    scheduler = TickScheduler(min_interval=0.6)
    client = select_client(config)
    system_prompt = build_system_prompt()
    try:
        while True:
            scheduler.wait_for_next_tick()
            frame = capturer.grab_resized((224, 224))
            # TODO: subscribe to plugin if enabled
            action = client.generate_action(system_prompt, frame, objects=None)
            click = action.get("click", [112, 112])
            move_and_click((click[0], click[1]), config.window.as_dict(), duration=0.15)
            logger.info(json.dumps(action))
    except KeyboardInterrupt:
        logger.info("Live capture stopped by user.")


class AppGUI:
    """Tkinter GUI for controlling demo and live modes."""

    def __init__(self, root: tk.Tk, config_path: str):
        self.root = root
        self.config_path = config_path
        self.thread: Optional[threading.Thread] = None
        self.running = False
        self._build()

    def _build(self) -> None:
        self.root.title("Qwen‑Plays‑OSRS")
        self.root.geometry("300x180")
        tk.Label(self.root, text="Qwen‑Plays‑OSRS", font=("Arial", 14, "bold")).pack(pady=10)
        self.demo_btn = tk.Button(self.root, text="Start demo", width=20, command=self.start_demo)
        self.demo_btn.pack(pady=5)
        self.live_btn = tk.Button(self.root, text="Start live", width=20, command=self.start_live)
        self.live_btn.pack(pady=5)
        self.stop_btn = tk.Button(self.root, text="Stop", width=20, state=tk.DISABLED, command=self.stop)
        self.stop_btn.pack(pady=5)
        tk.Label(self.root, text="Close window or press Ctrl+C to exit.").pack(pady=10)

    def start_demo(self) -> None:
        if self.running:
            return
        self.running = True
        self.demo_btn.config(state=tk.DISABLED)
        self.live_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.thread = threading.Thread(target=self._run_demo_thread, daemon=True)
        self.thread.start()

    def start_live(self) -> None:
        if self.running:
            return
        self.running = True
        self.demo_btn.config(state=tk.DISABLED)
        self.live_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.thread = threading.Thread(target=self._run_live_thread, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        if not self.running:
            return
        # The threads monitor running flag to exit gracefully
        self.running = False
        self.stop_btn.config(state=tk.DISABLED)
        self.demo_btn.config(state=tk.NORMAL)
        self.live_btn.config(state=tk.NORMAL)

    def _run_demo_thread(self) -> None:
        config = load_config(self.config_path)
        run_dir = prepare_run_dir(config.log_dir)
        logger = setup_logging(run_dir)
        system_prompt = build_system_prompt()
        client = select_client(config)
        demo_dir = Path(__file__).resolve().parent.parent / "demo_frames"
        frames = sorted([p for p in demo_dir.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg"}])
        if not frames:
            messagebox.showerror("Error", "No demo frames found.")
            self.stop()
            return
        for idx, frame_path in enumerate(frames[:10]):
            if not self.running:
                break
            img = cv2.imread(str(frame_path))
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            resized = cv2.resize(img_rgb, (224, 224))
            action = client.generate_action(system_prompt, resized, objects=None)
            click = tuple(action.get("click", [112, 112]))
            annotated = draw_click(resized, click)
            out_path = Path(run_dir) / f"gui_demo_{idx+1:04d}.png"
            cv2.imwrite(str(out_path), cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR))
            logger.info(f"Demo frame {idx+1}: {json.dumps(action)}")
            # Sleep to display pacing
            time.sleep(1.0 / max(config.fps, 1e-3))
        self.stop()

    def _run_live_thread(self) -> None:
        config = load_config(self.config_path)
        run_dir = prepare_run_dir(config.log_dir)
        logger = setup_logging(run_dir)
        capturer = ScreenCapturer(config.window.as_dict(), fps=config.fps)
        scheduler = TickScheduler(min_interval=0.6)
        client = select_client(config)
        system_prompt = build_system_prompt()
        try:
            while self.running:
                scheduler.wait_for_next_tick()
                frame = capturer.grab_resized((224, 224))
                action = client.generate_action(system_prompt, frame, objects=None)
                click = action.get("click", [112, 112])
                move_and_click((click[0], click[1]), config.window.as_dict(), duration=0.15)
                logger.info(json.dumps(action))
        except Exception as exc:
            logger.exception("Error in live thread", exc_info=exc)
        finally:
            self.stop()


def parse_args(args: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Qwen‑Plays‑OSRS prototype")
    parser.add_argument("--config", type=str, required=True, help="Path to YAML config file")
    parser.add_argument("--demo", action="store_true", help="Run the offline demo harness")
    parser.add_argument("--live", action="store_true", help="Run live capture without GUI")
    return parser.parse_args(args)


def main(argv: Optional[List[str]] = None) -> None:
    opts = parse_args(argv or sys.argv[1:])
    if opts.demo:
        run_demo(opts.config)
    elif opts.live:
        run_live(opts.config)
    else:
        root = tk.Tk()
        gui = AppGUI(root, opts.config)
        root.mainloop()


if __name__ == "__main__":
    main()