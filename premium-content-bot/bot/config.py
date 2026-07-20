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


def _mask(value: str, keep: int = 4) -> str:
    if not value:
        return "(empty)"
    if len(value) <= keep:
        return "*" * len(value)
    return value[:keep] + "*" * (len(value) - keep)


def validate_and_report() -> list[str]:
    """
    Checks every required environment variable, logs a masked summary of
    what was loaded, and returns a list of human-readable problems (empty
    list means everything required is present). Called once at startup so
    a missing/malformed env var fails loudly and immediately instead of
    causing a mysterious hang or silent no-op later.
    """
    from bot.utils.logger import logger

    problems = []

    logger.info("---- Environment variable check ----")

    if config.API_ID:
        logger.info("API_ID: OK (%s)", config.API_ID)
    else:
        logger.error("API_ID: MISSING or invalid (must be a nonzero integer)")
        problems.append("API_ID is missing or invalid")

    if config.API_HASH:
        logger.info("API_HASH: OK (%s)", _mask(config.API_HASH))
    else:
        logger.error("API_HASH: MISSING")
        problems.append("API_HASH is missing")

    if config.BOT_TOKEN:
        logger.info("BOT_TOKEN: OK (%s)", _mask(config.BOT_TOKEN))
    else:
        logger.error("BOT_TOKEN: MISSING")
        problems.append("BOT_TOKEN is missing")

    if config.MONGO_URI:
        logger.info("MONGO_URI: OK (%s)", _mask(config.MONGO_URI, keep=12))
    else:
        logger.error("MONGO_URI: MISSING")
        problems.append("MONGO_URI is missing")

    if config.ADMIN_IDS:
        logger.info("ADMIN_IDS: OK (%d admin(s) configured)", len(config.ADMIN_IDS))
    else:
        logger.warning("ADMIN_IDS: none configured — the admin panel will be inaccessible to everyone")

    logger.info("-------------------------------------")
    return problems
