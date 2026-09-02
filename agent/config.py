"""
config.py

Single place that loads .env and exposes every credential/setting the
project needs. Every script that needs credentials should do:

    from config import CLICKHOUSE_HOST, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD, GOOGLE_API_KEY

instead of reading os.environ directly -- this guarantees .env is loaded
exactly once, from the right path, regardless of which directory the script
is run from.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# .env lives at the project root (one level up from agent/ and data-generator/).
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_PATH = _PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=_ENV_PATH)

CLICKHOUSE_HOST = os.environ.get("CLICKHOUSE_HOST", "")
CLICKHOUSE_USER = os.environ.get("CLICKHOUSE_USER", "default")
CLICKHOUSE_PASSWORD = os.environ.get("CLICKHOUSE_PASSWORD", "")

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

# Model is env-configurable, not hardcoded per-file, because Gemini's model
# lineup and free-tier quotas have already shifted twice during this project:
# gemini-2.5-flash was deprecated for new API keys (404), and its replacement
# gemini-3.6-flash turned out to have only a 20-requests/DAY free quota --
# nowhere near enough for a multi-step agent pipeline. Flash-Lite models
# consistently carry the most generous free-tier daily quotas. Check your
# real live numbers at https://ai.dev/rate-limit (shown in any 429 error) --
# published figures vary by source/date and are not reliable to hardcode.
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")

# Defensive: strip a port suffix if someone pastes it into CLICKHOUSE_HOST
# (see load_clickhouse.py history -- this exact mistake happened once already).
if ":" in CLICKHOUSE_HOST:
    CLICKHOUSE_HOST = CLICKHOUSE_HOST.split(":")[0]


def require_clickhouse():
    if not CLICKHOUSE_HOST or not CLICKHOUSE_PASSWORD:
        raise SystemExit(
            f"Missing ClickHouse credentials. Checked for a .env file at: {_ENV_PATH}\n"
            "Make sure .env exists (copy .env.example -> .env) and contains:\n"
            "  CLICKHOUSE_HOST=...\n"
            "  CLICKHOUSE_USER=...\n"
            "  CLICKHOUSE_PASSWORD=..."
        )


def require_google():
    if not GOOGLE_API_KEY:
        raise SystemExit(
            f"Missing GOOGLE_API_KEY. Checked for a .env file at: {_ENV_PATH}\n"
            "Get a free key at https://aistudio.google.com, then add to .env:\n"
            "  GOOGLE_API_KEY=..."
        )