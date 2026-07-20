"""
BUG-11 FIX: Structured log events sent to LOG_CHANNEL.

LOG_CHANNEL is an optional Telegram channel/group where the bot posts
key operational events (new users, key redemptions, broadcasts).
Silently no-ops when LOG_CHANNEL is 0 or unset.
"""
from bot.config import config
from bot.utils.logger import logger


async def send_log(client, text: str) -> None:
    """Post *text* to LOG_CHANNEL. Never raises — logging must never crash the main flow."""
    if not config.LOG_CHANNEL:
        return
    try:
        from pyrogram.enums import ParseMode
        await client.send_message(config.LOG_CHANNEL, text, parse_mode=ParseMode.MARKDOWN)
    except Exception as exc:
        logger.warning("Failed to post to LOG_CHANNEL %s: %s", config.LOG_CHANNEL, exc)
