"""
BUG-11 FIX: Utility for sending structured log events to LOG_CHANNEL.

LOG_CHANNEL is an optional Telegram channel/group ID where the bot
posts important operational events (new users, key redemptions, broadcasts,
etc.). If LOG_CHANNEL is 0 / unset, all calls are silent no-ops.
"""
from bot.config import config
from bot.utils.logger import logger


async def send_log(client, text: str) -> None:
    """Send *text* to LOG_CHANNEL. Silently ignores errors (never crash the main flow)."""
    if not config.LOG_CHANNEL:
        return
    try:
        from pyrogram.enums import ParseMode
        await client.send_message(config.LOG_CHANNEL, text, parse_mode=ParseMode.MARKDOWN)
    except Exception as exc:
        logger.warning("Failed to send log to LOG_CHANNEL %s: %s", config.LOG_CHANNEL, exc)
