# Session 04 Agent Architecture Lab

This folder contains simple, readable training code for the three labs described in the session notes.

## Project structure

- `lab1_react_agent.py` — ReAct-style agent with tool calls
- `lab2_langgraph_multiagent.py` — supervisor/worker style multi-agent flow
- `lab3_tool_design.py` — tool design patterns and a small tool registry
- `data/support_tickets.json` — sample support tickets

## Setup

From this folder, create a virtual environment and install the dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

On macOS/Linux, use:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the labs

```bash
python lab1_react_agent.py
python lab2_langgraph_multiagent.py
python lab3_tool_design.py
```

## Environment variables

Copy `.env.example` to `.env` and fill in your values if you later want to connect to real LLM APIs:

```bash
copy .env.example .env
```

> The scripts in this training version are intentionally lightweight and run without needing a live OpenAI key.
