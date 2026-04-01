# Composio agent comparison

This repository contains several sample agents that use [Composio](https://composio.dev) with different stacks: OpenAI Agents, Google ADK (Gemini), and Claude (Anthropic) via the Claude Agent SDK.

## Prerequisites

- Python 3.10+ recommended  
- A [Composio](https://app.composio.dev) account and API key  
- Virtual environment (the repo uses `.venv`; keep it out of git)

## Setup (once)

From the repository root (`comparison/`):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

On macOS/Linux, activate with `source .venv/bin/activate`.

---

## `openai_agent` — Job search assistant (OpenAI Agents + Composio MCP)

**What it does:** Runs a **guided job-search flow** using the OpenAI Agents SDK (`gpt-5`), Composio Tool Router over MCP, and toolkits **GitHub**, **Exa**, **Google Sheets**, and **browser_tool**. It walks users through onboarding (one question per turn), then helps discover roles, track a shortlist in Sheets, and use the browser for applications when appropriate.

**Environment variables** (e.g. `openai_agent/.env` or export before running):

| Variable | Required |
|----------|----------|
| `COMPOSIO_API_KEY` | Yes |
| `COMPOSIO_USER_ID` | Yes |

**Run:**

```powershell
cd openai_agent
python main.py
```

Or from the repo root:

```powershell
python openai_agent\main.py
```

Chat in the terminal; use `exit`, `quit`, or `q` to stop.

**Optional utility:** `openai_agent/tools_slug.py` prints Composio tool metadata for the configured toolkits (handy for debugging).

---

## `google_agent` — Composio + Gemini (Google ADK)

**What it does:** Defines a **Google ADK** `Agent` using **Gemini** and Composio’s **Google** provider. The session exposes Composio MCP tools for **gmail** (e.g. search/execute tools, connections, remote workbench as exposed by your Composio session).

**Environment variables** (use `google_agent/.env` or the shell):

| Variable | Required |
|----------|----------|
| `GOOGLE_API_KEY` | Yes (Gemini / Google GenAI) |
| `COMPOSIO_API_KEY` | Yes |
| `COMPOSIO_USER_ID` | Yes |

**Run — terminal (ADK CLI):**

From the **repository root** (the folder that contains `google_agent/`), not inside `google_agent/`:

```bash
adk run google_agent
```

**Run — web UI (development only):**

```bash
adk web
```

Open the URL shown (default `http://127.0.0.1:8000`) and select **`google_agent`**.  
Do **not** run `adk web` from inside `google_agent/` only; ADK expects a directory that **contains** agent subfolders.

---

### `agent.py` — Simple Claude chat with Composio MCP

**What it does:** Interactive CLI using **Claude Agent SDK** + Composio MCP. The code creates a session with the **GitHub** toolkit (connect GitHub in Composio if tools require it).

**Environment variables:**

| Variable | Required |
|----------|----------|
| `COMPOSIO_API_KEY` | Yes |
| `COMPOSIO_USER_ID` or `USER_ID` | Yes |
| Anthropic credentials | Required by Claude Agent SDK (e.g. `ANTHROPIC_API_KEY` per SDK docs) |

**Run:**

```powershell
python claude_oss_contributor\agent.py
```

### `oss_contributor.py` — OSS contributor workflow

**What it does:** Same stack, tuned for **open-source contribution**: discover issues (default toolkits **github** + **composio_search**), read repo rules, implement small changes, and prepare PRs. Optional `OSS_COMPOSIO_TOOLKITS` (comma-separated) overrides default toolkits; `OSS_MAX_TURNS` caps turns (default `40`).

Loads env from **`claude_oss_contributor/.env`** explicitly.

**Run:**

```powershell
python -m claude_oss_contributor.oss_contributor
```

Or:

```powershell
cd claude_oss_contributor
python oss_contributor.py
```

---

## Troubleshooting

- **ADK web: “No agents found”** — Run `adk web` from the folder that **contains** `google_agent`, not from inside `google_agent`.  
- **Missing tools / auth** — Connect the relevant apps in the Composio dashboard; some flows use `manage_connections` (OpenAI agent) or manual connection for Gmail/GitHub.  
- **Secrets** — Keep API keys in `.env` files; this repo’s `.gitignore` ignores `.env` and `.venv`.
