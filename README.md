# ⚡ DevinX Ultimate — Elite AI Software Engineer

An elite autonomous AI software engineer that runs in your browser. Give it engineering tasks and it will plan, code, test, and commit — all in a sandboxed workspace with 32 tools, 3-tier safety, and persistent memory.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-purple)
![Groq](https://img.shields.io/badge/Groq-Llama_3.3-orange)

## Features

### Core
- **🧠 AI-Powered Planning** — Breaks down tasks into subtasks with estimation and tracking
- **📁 File Operations** — Read, write, and edit files in the sandboxed workspace
- **💻 Terminal (3-Tier Safety)** — `safe` (immediate), `requires_approval` (user confirms), `critical` (must type "CONFIRM CRITICAL")
- **🌐 Web Browsing** — Search, fetch pages, take screenshots, and compare visual output
- **🔀 Git Integration** — Status, branch, add, commit, diff

### New in v0.2.0
- **🗄️ Database Interaction** — Read-only queries (SELECT) + approved mutations (INSERT/UPDATE/DDL)
- **🚀 CI/CD & Deployment** — Pipeline status, trigger builds, get logs, preview/staging deploys
- **🏥 Health Monitoring** — Check service endpoints for status and response time
- **📸 Screenshots & Visual Comparison** — Capture pages and compare with similarity scoring
- **🧠 Memory & Learning** — Persistent knowledge store (memorize/recall), learns from mistakes
- **📝 Assumptions Tracking** — Log and verify assumptions before finalizing work
- **📊 Report Generation** — Standalone HTML reports with tasks, assumptions, and status
- **🔗 Jira & Slack Integration** — Update issues and notify channels
- **🔧 Self-Diagnosis & Recovery** — Verify all subsystems, restore state after restarts
- **📋 32 Tools** — Full tool suite available via OpenAI function calling

## Architecture

```
ai-bot/
├── app/
│   ├── main.py              # FastAPI app + WebSocket endpoint
│   ├── engine.py             # AI reasoning loop (OpenAI + tool calls)
│   ├── config.py             # Environment configuration
│   ├── system_prompt.py      # System prompt + 32 tool definitions
│   ├── models/
│   │   └── schemas.py        # Pydantic models
│   └── tools/
│       ├── executor.py       # Central tool router (32 tools)
│       ├── task_manager.py   # Task CRUD operations
│       ├── assumptions.py    # Assumptions tracking
│       ├── file_ops.py       # File read/write/edit
│       ├── terminal.py       # Shell execution (3-tier safety)
│       ├── git_ops.py        # Git operations
│       ├── web_browse.py     # Web search & page fetching
│       ├── screenshots.py    # Screenshots & visual comparison
│       ├── database.py       # DB queries & mutations
│       ├── ci_cd.py          # CI/CD pipeline management
│       ├── monitoring.py     # Health checks
│       ├── memory.py         # Persistent knowledge store
│       ├── integrations.py   # Jira, Slack, reports
│       └── diagnostics.py    # Self-test & state recovery
├── static/
│   ├── index.html            # Chat UI
│   ├── style.css             # Styles (dark theme)
│   └── app.js                # Client-side WebSocket logic
├── workspace/                # Sandboxed working directory
├── pyproject.toml
├── .env.example
└── README.md
```

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/Cohoci4/ai-bot.git
cd ai-bot
```

### 2. Install dependencies

```bash
pip install -e .
```

### 3. Configure environment

```bash
cp .env.example .env
```

**Option A: Groq (free, recommended for testing)**
1. Get a free API key at https://console.groq.com
2. Edit `.env`:
```env
OPENAI_API_KEY=gsk_your-groq-key
OPENAI_MODEL=llama-3.3-70b-versatile
LLM_BASE_URL=https://api.groq.com/openai/v1
```

**Option B: OpenAI (paid)**
```env
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4o
# LLM_BASE_URL not needed — uses OpenAI by default
```

### 4. Run the server

```bash
python -m app.main
# or
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Open in browser

Navigate to `http://localhost:8000` and start chatting!

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | API key (OpenAI, Groq, or any OpenAI-compatible provider) |
| `OPENAI_MODEL` | `gpt-4o` | Model name (`gpt-4o`, `llama-3.3-70b-versatile`, etc.) |
| `LLM_BASE_URL` | — | Custom API base URL (e.g. `https://api.groq.com/openai/v1`) |
| `WORKSPACE_DIR` | `./workspace` | Sandboxed directory for file operations |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |

## How It Works

1. **User sends a message** via the chat UI
2. **WebSocket** delivers it to the FastAPI backend
3. **AI Engine** sends the conversation to OpenAI with 32 tool definitions
4. **OpenAI responds** with text and/or tool calls
5. **Tool Executor** routes to the appropriate tool implementation
6. **Results stream back** to the UI in real-time
7. The loop continues until the AI finishes its response

## Safety (3-Tier System)

| Level | Behavior | Examples |
|-------|----------|---------|
| **safe** | Executes immediately | `ls`, `git status`, `npm test`, `cat` |
| **requires_approval** | Pauses for user confirmation | `npm install`, `git push`, config changes |
| **critical** | User must type "CONFIRM CRITICAL" | `rm -rf`, `drop database`, force push |

Additional safety:
- File operations restricted to `workspace/` directory
- Path traversal prevention (`Path.is_relative_to()`)
- Database mutations always require approval
- Health checks block internal network addresses
- CI/CD triggers and deployments require approval
- Subprocess cleanup on timeout (kill + wait)

## License

MIT
