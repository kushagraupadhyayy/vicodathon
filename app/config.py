from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "vicodathon.db"


@dataclass(frozen=True)
class Settings:
    db_path: Path = DEFAULT_DB_PATH
    tick_minutes: int = int(os.getenv("TICK_MINUTES", "60"))
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")
    newsapi_key: str | None = os.getenv("NEWSAPI_KEY")
    render_keepalive_url: str | None = os.getenv("RENDER_KEEPALIVE_URL")


settings = Settings()
