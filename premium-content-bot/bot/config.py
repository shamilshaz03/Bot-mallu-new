"""
Central configuration loaded from environment variables.
Never hardcode secrets — everything comes from .env / host env vars.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _split_ids(raw: str) -> list[int]:
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


class Config:
    API_ID: int = int(os.environ.get("API_ID", "0"))
    API_HASH: str = os.environ.get("API_HASH", "")
    BOT_TOKEN: str = os.environ.get("BOT_TOKEN", "")

    MONGO_URI: str = os.environ.get("MONGO_URI", "")
    DB_NAME: str = os.environ.get("DB_NAME", "premium_content_bot")

    ADMIN_IDS: list[int] = _split_ids(os.environ.get("ADMIN_IDS", ""))

    LOG_CHANNEL: int = int(os.environ.get("LOG_CHANNEL", "0") or 0)
    FORCE_JOIN_CHANNEL: str = os.environ.get("FORCE_JOIN_CHANNEL", "")
    MAINTENANCE_MODE: bool = os.environ.get("MAINTENANCE_MODE", "false").lower() == "true"

    PORT: int = int(os.environ.get("PORT", "8000"))

    ITEMS_PER_PAGE: int = 10

    PLAN_IDS = ["199", "299", "799"]
    PLAN_RANK = {"199": 1, "299": 2, "799": 3}  # for upgrade comparisons


config = Config()
