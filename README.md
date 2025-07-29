# Qwen‑Plays‑OSRS

Qwen‑Plays‑OSRS is a small research prototype that connects the multimodal large language model **Qwen‑2.5‑VL** to the Old School RuneScape client.  It captures an area of the game window, optionally subscribes to a RuneLite plugin’s object feed, sends a down‑scaled image to Qwen, and applies the resulting click recommendation via a human‑like mouse movement.  The goal of this repository is to demonstrate the feasibility of simple vision→action loops on a desktop game client.  **This project is for education only and must be run on an offline or private RuneScape server;** using any automation on the live game may violate Jagex’s terms of service.

The prototype is composed of a Python app, a thin model adapter, a minimal RuneLite plugin for publishing visible objects, configuration and demo assets, and a handful of tests.  It supports Windows 11 and Ubuntu 22.04+, and runs on the user’s NVIDIA RTX 3090 GPU or CPU via the model backend of your choice (Ollama, vLLM, remote API, etc.).  A small Tkinter GUI allows you to pick the OSRS window rectangle, start/stop the loop and run an offline demo.

## Project structure

```
qwen-plays-osrs/
  README.md                    – this file
  LICENSE                      – MIT licence
  docs/
    design.md                 – detailed architecture & threat model
    architecture.png          – high level architecture diagram
  prompts/
    system_qwen.md            – the system prompt given to Qwen‑2.5‑VL
  app/
    main.py                   – entry‑point, Tkinter GUI and CLI
    config.py                 – load YAML configuration into dataclasses
    capture.py                – screen capture & preprocessing using mss
    control.py                – human‑like mouse movements via pyautogui
    scheduler.py              – tick pacing and rate limiting
    overlay.py                – optional overlay drawing for debug
    llm_clients/
      __init__.py
      ollama_client.py        – call a local Ollama model
      open_api_client.py      – generic HTTP client for remote models
    utils/
      geometry.py             – clamping and rectangle helpers
      beziers.py              – simple Bezier path generator
      logging_utils.py        – run‑specific logging setup
  runelite-plugin/
    build.gradle              – Gradle build file for RuneLite plugin
    settings.gradle           – include plugin project
    src/main/java/com/example/qposrs/QpOsrsPlugin.java
                              – Plugin toggles capture and publishes JSON
    src/main/java/com/example/qposrs/ZmqPublisher.java
                              – ZeroMQ publisher for object tables
    src/main/resources/
                              – placeholder resources (manifest)
  configs/
    app.windows.yaml          – default config for Windows
    app.linux.yaml            – default config for Linux
  demo_frames/
    frame_0001.png …          – pre‑recorded OSRS‑like frames for demo
  scripts/
    run_windows.bat           – create venv and run on Windows
    run_linux.sh              – create venv and run on Linux
  tests/
    test_action_schema.py     – validates model outputs against schema
    test_clip_bounds.py       – ensures clicks stay in the window
    test_tick_pacing.py       – ensures no double‑clicks too quickly
```

## Installation and usage

These instructions assume you have **Python 3.11** installed.  On Windows, use Command Prompt or PowerShell; on Linux, use the shell.  Replace `<config>` with the appropriate YAML file for your platform (`configs/app.windows.yaml` or `configs/app.linux.yaml`).

### 1. Clone and prepare

```
git clone https://example.com/qwen-plays-osrs.git
cd qwen-plays-osrs
```

On Windows run:

```
scripts\run_windows.bat --config configs\app.windows.yaml
```

On Linux run:

```
bash scripts/run_linux.sh --config configs/app.linux.yaml
```

The script will create a virtual environment in `.venv`, install required packages (`mss`, `pyautogui`, `opencv‑python`, `pyyaml`, `pyzmq`, `pydantic`, `jsonschema`, etc.), and launch a small Tkinter GUI.  Use the “Select window” button to pick the OSRS window (a rectangle picker appears on screen) or enter coordinates manually in the YAML file.  Click **Start demo** to run the offline replay harness on the provided images; it prints the model’s proposed clicks and draws red dots on each frame.  Click **Start live** to start capturing your OSRS window at 2–4 FPS and sending clicks.  Press **F10** or the **Stop** button to pause.

### 2. RuneLite plugin

The optional RuneLite plugin enhances perception by publishing a list of visible objects on each game tick.  To build it you need **Java 17** and **Gradle**:

```
cd runelite-plugin
./gradlew build
```

The resulting JAR can be placed into a RuneLite development client or submitted to the Plugin Hub.  It exposes a simple toggle in the plugin panel and publishes JSON arrays to `tcp://127.0.0.1:5555` via ZeroMQ.  Our Python app subscribes on the same port if `plugin_enabled: true` in the config.

### 3. Model setup

This project assumes you have Qwen‑2.5‑VL running locally (e.g. via **Ollama** or **vLLM**).  Specify the model endpoint in the YAML config (`model: {backend: "ollama", url: "http://localhost:11434/api/generate", model_name: "qwen2.5-vl"}`) or provide `backend: "open_api"` with a `url` and optional headers for a remote service.  The app will read the `prompts/system_qwen.md` file to build the system prompt and send the 224×224 PNG along with any plugin JSON.

## Research and dependencies

This repository was created in OpenAI’s computer‑using agent mode.  The agent can control the cursor to click on websites and run terminal commands, but it cannot type arbitrary OS-level commands without user approval【190784088567649†L212-L244】.  Our design uses only high‑level screen capture and input functions.

* **Screen capture (mss)** – We use the **mss** library for its cross‑platform, high‑performance screen grabbing.  A monitor dictionary defines the region to capture (`top`, `left`, `width`, `height`), and `sct.grab(monitor)` returns raw pixel data【808604261174784†L408-L416】.  The library advertises itself as an ultra‑fast screenshot module suitable for game or AI integrations【898360885280542†L28-L39】.
* **Mouse control (PyAutoGUI)** – PyAutoGUI provides simple functions like `moveTo(x, y, duration)` and `click()` for simulating mouse movement and clicks.  Coordinates start at the top‑left of the primary monitor; specifying a `duration` produces a smooth, human‑like path【709101597065702†L112-L126】【709101597065702†L196-L224】.
* **ZeroMQ (pyzmq)** – For the RuneLite plugin we use a publisher–subscriber pattern.  A publisher binds to `tcp://*:5555` and repeatedly sends JSON messages with `send()`, while the client uses a subscriber socket to connect and call `recv()`【248017015356212†L61-L116】.
* **OSRS Wiki / MediaWiki API** – The optional retrieval‑augmented generation (RAG) module calls the official OSRS Wiki API at `https://oldschool.runescape.wiki/api.php`【862768907690804†L115-L124】.  We respect the API’s guidelines by adding a custom user‑agent and obeying rate limits【862768907690804†L48-L60】.  Using the API avoids scraping and provides structured data【862768907690804†L21-L24】.
* **RuneLite plugin guidelines** – When writing the RuneLite plugin we followed the developer guide.  Plugins consist of a class annotated with `@PluginDescriptor`, optional config and overlay classes, and event subscribers annotated with `@Subscribe`【430030540427568†L231-L247】.  New plugin development should happen in the Plugin Hub, which invites community submissions【430030540427568†L189-L194】.

Please see `docs/design.md` for a deeper discussion of design decisions, threat modelling, and trade‑offs.

## Safety and compliance

This prototype is intended for private/offline servers and research.  Do **not** use it on Jagex’s official game servers.  The script only uses screen capture and standard OS input events; it does not read memory or inject code.  Tick pacing ensures at least **0.55 s** between actions to mimic human reaction times.  A panic key (F10) stops all automation.  The optional OSRS Wiki queries respect API limits and include a custom user agent.  See `docs/design.md` for more details.
