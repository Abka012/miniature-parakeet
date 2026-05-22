# miniature-parakeet

Async Multi-Agent POC using LangGraph + FastMCP + real media processing.

## Overview

A lightweight async multi-agent system that processes images, audio, and video via base64-encoded payloads. Uses LangGraph for workflow orchestration, FastMCP for tool registration, and real processing libraries (Pillow, OpenCV, stdlib `wave`).

## Architecture

```
                User Request
                      |
              SupervisorAgent
                      |
       Fan-out (parallel conditional edge)
      ┌──────────┼──────────┐
      |          |          |
  ImageAgent  AudioAgent VideoAgent
      |          |          |
  Pillow     stdlib wave  OpenCV
  processor   processor   processor
      |          |          |
      └──────────┼──────────┘
           Fan-in to Aggregator
```

## Features

- ✅ Real media processing (Pillow, OpenCV, stdlib wave)
- ✅ Parallel agent execution via LangGraph fan-out
- ✅ MCP (Model Context Protocol) integration via FastMCP
- ✅ Robust error handling (corrupt base64, invalid formats)
- ✅ Shared state with `Annotated` reducers for concurrent writes
- ✅ Minimal base64 payload generators for testing (stdlib-only)

## Requirements

```
langgraph
langchain
fastmcp
Pillow
opencv-python-headless
numpy
```

## Setup

### 1. Create and activate a virtual environment

```bash
# Create the virtual environment
python -m venv .venv

# Activate it
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows (cmd)
.venv\Scripts\Activate.ps1       # Windows (PowerShell)

# Deactivate when done
deactivate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

## Project Structure

```
project/
├── app/
│   ├── agents/
│   │   ├── image_agent.py
│   │   ├── audio_agent.py
│   │   ├── video_agent.py
│   │   └── supervisor.py
│   │
│   ├── tools/
│   │   ├── mcp_server.py          # FastMCP server + real processor wiring
│   │   ├── mcp_client.py          # Async client wrapper
│   │   ├── image_tool.py
│   │   ├── audio_tool.py
│   │   ├── video_tool.py
│   │   └── processors/            # Decoupled processing logic
│   │       ├── image_processor.py  # Pillow-based
│   │       ├── audio_processor.py  # stdlib wave
│   │       └── video_processor.py  # OpenCV-based
│   │
│   ├── graph/
│   │   └── workflow.py
│   │
│   ├── state/
│   │   ├── state.py
│   │   └── shared_memory.py
│   │
│   ├── utils/
│   │   └── requirements.py
│   │
│   └── __init__.py
│
├── scripts/
│   └── test_workflow.py           # Payload verification & integration tests
│
├── main.py                         # Demo entry point
├── requirements.txt
├── pyproject.toml                  # Python + basedpyright config
└── README.md
```

## Usage

### Run the demo

```bash
python main.py
```

Output shows three examples:
1. **Text-based routing** — auto-detects task type from user input
2. **Parallel processing** — fans out to all 3 agents with real base64 payloads
3. **Supervisor workflow** — routes to a single agent

### Run tests

```bash
python scripts/test_workflow.py
```

8 tests covering payload integrity, metadata extraction, parallel transport, partial payloads, and error handling.

### Programmatic use

```python
from app.graph.workflow import Workflow

wf = Workflow()

# Text-based — auto-routes to image/audio/video agent
result = await wf.run("Analyze this image")

# Parallel — feeds base64 to all three agents
result = await wf.run_parallel(
    image_data="base64_encoded_png",
    audio_data="base64_encoded_wav",
    video_data="base64_encoded_mp4",
)
```

## Processing Pipeline

| Media   | Library               | Extracted Metadata                                    |
|---------|-----------------------|-------------------------------------------------------|
| Image   | Pillow                | width, height, format, mode, thumbnail                |
| Audio   | stdlib `wave`         | duration, sample rate, channels, sample width, frames |
| Video   | opencv-python-headless | duration, fps, resolution, frame count, dimensions    |

All processors return structured dicts: `{"status": "success", "metadata": {...}}` or `{"status": "error", "error": "..."}`.

## Static Analysis

The project uses `basedpyright` for type checking:

```bash
pip install basedpyright
basedpyright .
```

Configuration lives in `pyproject.toml` under `[tool.pyright]`.

## State Management

`AgentState` extends `MessagesState` with custom fields. Fields written concurrently during parallel fan-out use `Annotated` reducers for safe merging:

- `results` — `_merge_results` dict merge
- `metadata` — `_merge_results` dict merge
- `current_agent` — `_last_wins`
- `error` — `_last_wins`
