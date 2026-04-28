"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
LLM_BASE_URL: str | None = os.getenv("LLM_BASE_URL") or None
WORKSPACE_DIR: Path = Path(os.getenv("WORKSPACE_DIR", "./workspace")).resolve()
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8000"))

# Ensure workspace exists
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
