# Design of Qwen‑Plays‑OSRS

## Goals and scope

The aim of this prototype is to explore how a vision‑language model can operate a traditional desktop game client through a simple perception–reasoning–actuation loop.  Our focus is on **Old School RuneScape** (OSRS), a point‑and‑click MMORPG.  We intend to:

* Capture the game window at a moderate frame rate (2–4 FPS) without interfering with other applications.
* Optionally ingest structured observations from the client via a RuneLite plugin.
* Convert the observation into a **224×224** image and pass it to **Qwen‑2.5‑VL** along with a carefully crafted system prompt and any plugin JSON.  The model returns a strict JSON action containing a click coordinate and short rationale.
* Execute the click using human‑like mouse motion while enforcing tick pacing (≥0.55 s between actions).
* Provide a basic GUI and replay harness to allow users to inspect behaviour safely and offline.

The project is not intended to produce a competitive OSRS bot.  We do not automate high‑level decision making or planning; the optional RAG tool only performs simple wiki lookups.  We avoid reading or writing the game’s memory and respect network and plugin hub guidelines.

## High‑level architecture

The prototype comprises three cooperating layers:

1. **Perception layer** – A screen capture module uses the **mss** library to grab a rectangular region corresponding to the OSRS window.  The image is optionally masked to hide the chatbox and scaled to 224×224 pixels.  When the RuneLite plugin is enabled, a ZeroMQ subscriber receives a JSON list of visible objects and bounding boxes on every game tick.
2. **Reasoning layer** – The Qwen adapter packages the 224×224 image and optional plugin JSON into a prompt.  It sends the request to a locally running model (via **Ollama**) or a remote endpoint (generic HTTP).  The system prompt (see `prompts/system_qwen.md`) instructs the model to output only JSON with fields `click`, `modifiers`, and `reason`.  A simple parser validates the response using a JSON schema and clamps the click within the window rectangle.
3. **Actuation layer** – A tick scheduler ensures at least 0.6 s between actions.  The `control` module moves the mouse along a Bezier curve with small jitter and performs a click via **PyAutoGUI**.  The click is restricted to the configured window bounds and can be cancelled with a global panic key (F10).

```
┌───────────────┐      ┌─────────────────────┐      ┌────────────────────┐
│ Capture (mss) │────▶│  Qwen adapter +     │────▶│  Mouse control     │
│ + plugin feed │      │  JSON parsing       │      │  & scheduler       │
└───────────────┘      └─────────────────────┘      └────────────────────┘
        ▲                     ▼                              │
        │               (224×224 img + JSON)                │
        │                     │                              │
        └────────── replay harness ────────────▶ Log & UI ──┘
```

The optional RAG module (hidden behind a flag) can query the OSRS Wiki using the MediaWiki API to answer simple questions (e.g. “where is the nearest chicken coop?”).  It is invoked only when the model asks for external knowledge and not in the core loop.

### Module responsibilities

| Module              | Responsibility                                                |
|---------------------|---------------------------------------------------------------|
| `capture.py`        | Use **mss** to capture a region defined by `top`, `left`, `width`, `height`; mask chatbox; downscale to 224×224【808604261174784†L408-L416】. |
| `config.py`         | Load YAML configuration into dataclasses; expose window rect, FPS, model backend. |
| `llm_clients/*`     | Provide two clients: one for **Ollama** with `POST /api/generate`, and a generic HTTP client for remote servers. |
| `scheduler.py`      | Enforce tick pacing by waiting until at least `min_interval` seconds have passed before allowing another action. |
| `control.py`        | Compute a human‑like path to the target using a Bezier curve; call `pyautogui.moveTo` and `click`【709101597065702†L112-L126】.  Clamp coordinates within the window. |
| `overlay.py`        | Draw debug information (click dots, bounding boxes) on frames using OpenCV; optional. |
| `logging_utils.py`  | Create run directories (`runs/YYYY‑MM‑DD_HH‑MM‑SS`), log frames, prompts and actions to disk. |
| `runelite-plugin`   | Publish visible objects to ZeroMQ each tick; toggle on/off via RuneLite UI; obey plugin hub guidelines【430030540427568†L231-L247】. |

### Config and run scripts

The YAML config files (`configs/app.windows.yaml` and `configs/app.linux.yaml`) specify the OSRS window rectangle, frame rate, model backend, and whether the RuneLite plugin should be used.  The `scripts/run_windows.bat` and `scripts/run_linux.sh` scripts create a Python virtual environment, install dependencies, and launch the GUI or CLI with the chosen config.  The scripts are intentionally simple and avoid privileges beyond Python installation.

### Threat model and ToS considerations

**User responsibility.**  The repository is intended for personal study on private/offline servers.  Running automation on official servers may breach RuneScape’s terms of service.  We emphasise that this code is provided “as is” and the user assumes all liability.

**No memory reading or injection.**  We do not read any process memory or modify the OSRS client.  All observations come from screen capture (mss)【808604261174784†L408-L416】 or the RuneLite plugin feed, which is built on top of RuneLite’s official API and plugin hub guidelines【430030540427568†L189-L194】.

**Rate limiting and human‑like input.**  The tick scheduler enforces a minimum delay of 0.55 s between actions.  Mouse movement uses PyAutoGUI with a duration parameter to generate smooth trajectories rather than instantaneous jumps【709101597065702†L112-L126】【709101597065702†L196-L224】.  The `beziers.py` helper adds small jitter to mimic human behaviour.

**API respect.**  The optional RAG module uses the OSRS Wiki via the MediaWiki API at `api.php`【862768907690804†L115-L124】 and adheres to its guidelines: we send a custom user agent and limit request rate to avoid overloading the wiki【862768907690804†L48-L60】.  We avoid scraping and instead use structured API responses【862768907690804†L21-L24】.

### Trade‑offs and design decisions

* **Thin adapter vs. direct integration.**  We chose to decouple the Python app from the Qwen‑2.5‑VL serving layer by defining two simple clients.  Users may run the model via Ollama (local) or call any HTTP endpoint.  This decoupling makes the prototype portable but introduces slight overhead in packaging images and parsing JSON.
* **ZeroMQ plugin feed vs. pure vision.**  The RuneLite plugin is optional.  It reduces latency and ambiguity by providing a table of objects and bounding boxes every game tick.  However, it requires running a dev client and building a plugin, which increases complexity.  Users can run purely vision‑based (simple screen capture) by disabling the plugin.
* **Tkinter GUI vs. CLI.**  A small GUI with “Start/Stop” buttons improves accessibility, particularly on Windows.  For power users or servers without a display, the CLI can run with `--demo` or `--live` flags.
* **Test coverage.**  We include simple unit tests for schema validation, coordinate clipping and tick pacing.  Given limited scope, we do not test the full end‑to‑end loop with a live model, but the demo harness provides offline feedback.

## Conclusion

Qwen‑Plays‑OSRS demonstrates that a multimodal language model can operate a legacy desktop game client in a safe, controlled manner.  By relying on screen capture, a system prompt that enforces JSON output, and careful rate limiting, the prototype illustrates both the possibilities and limitations of agent‑based automation.  Future work could extend this approach to more complex games, integrate higher‑level planning via RAG, or explore more robust computer vision pipelines.
