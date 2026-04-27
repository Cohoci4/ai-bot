# ⚡ DevinX — AI Software Engineer Bot

An autonomous AI software engineer that runs in your browser. Give it engineering tasks and it will plan, code, test, and commit — all in a sandboxed workspace.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-purple)

## Features

- **🧠 AI-Powered Planning** — Breaks down tasks into subtasks with tracking
- **📁 File Operations** — Read, write, and edit files in the sandboxed workspace
- **💻 Terminal Access** — Run shell commands with approval gating for destructive ops
- **🌐 Web Browsing** — Search the web and fetch documentation
- **🔀 Git Integration** — Status, branch, add, commit, diff
- **📋 Task Management** — Visual task board in the sidebar
- **⚡ Real-time Streaming** — WebSocket-based streaming responses
- **🔒 Safety** — Dangerous commands require explicit user approval

## Architecture

```
ai-bot/
├── app/
│   ├── main.py              # FastAPI app + WebSocket endpoint
│   ├── engine.py             # AI reasoning loop (OpenAI + tool calls)
│   ├── config.py             # Environment configuration
│   ├── system_prompt.py      # System prompt + tool definitions
│   ├── models/
│   │   └── schemas.py        # Pydantic models
│   └── tools/
│       ├── executor.py       # Central tool router
│       ├── task_manager.py   # Task CRUD operations
│       ├── file_ops.py       # File read/write/edit
│       ├── terminal.py       # Shell command execution
│       ├── git_ops.py        # Git operations
│       └── web_browse.py     # Web search & page fetching
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
# or
pip install fastapi uvicorn openai python-dotenv httpx beautifulsoup4 jinja2 websockets
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
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
| `OPENAI_API_KEY` | — | Your OpenAI API key (required) |
| `OPENAI_MODEL` | `gpt-4o` | Model to use |
| `WORKSPACE_DIR` | `./workspace` | Sandboxed directory for file operations |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |

## How It Works

1. **User sends a message** via the chat UI
2. **WebSocket** delivers it to the FastAPI backend
3. **AI Engine** sends the conversation to OpenAI with tool definitions
4. **OpenAI responds** with text and/or tool calls
5. **Tool Executor** runs the requested tools (files, terminal, git, etc.)
6. **Results stream back** to the UI in real-time
7. The loop continues until the AI finishes its response

## Safety

- File operations are restricted to the `workspace/` directory
- Dangerous terminal commands require explicit user approval
- Path traversal attacks are prevented
- Commands time out after 60 seconds

## License

MIT
