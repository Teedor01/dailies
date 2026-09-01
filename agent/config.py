import os
from pathlib import Path
from dotenv import load_dotenv


_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_PATH = _PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=_ENV_PATH)

CLICKHOUSE_HOST = os.environ.get("CLICKHOUSE_HOST", "")
CLICKHOUSE_USER = os.environ.get("CLICKHOUSE_USER", "default")
CLICKHOUSE_PASSWORD = os.environ.get("CLICKHOUSE_PASSWORD", "")

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")


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
