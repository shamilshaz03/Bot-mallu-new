import asyncio
from pyrogram import Client

from bot.config import config
from bot.utils.logger import logger
from bot.database.connection import ensure_indexes
from bot.database.seed import seed_defaults
from bot.webserver import run_webserver


app = Client(
    "premium_content_bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
    plugins=dict(root="bot/plugins"),
)


async def startup_tasks():
    logger.info("Ensuring MongoDB indexes...")
    await ensure_indexes()
    logger.info("Seeding default plans/settings (idempotent)...")
    await seed_defaults()
    logger.info("Startup checks complete.")


async def main():
    if not config.API_ID or not config.API_HASH or not config.BOT_TOKEN:
        raise SystemExit(
            "Missing API_ID / API_HASH / BOT_TOKEN. Copy .env.example to .env and fill it in."
        )
    if not config.MONGO_URI:
        raise SystemExit("Missing MONGO_URI. Set it in your environment or .env file.")
    if not config.ADMIN_IDS:
        logger.warning("No ADMIN_IDS configured — the admin panel will be inaccessible to everyone.")

    await startup_tasks()

    await run_webserver()
    logger.info("Health-check webserver listening on port %s", config.PORT)

    await app.start()
    logger.info("Bot started successfully. Waiting for updates...")

    await asyncio.Event().wait()  # run forever


if __name__ == "__main__":
    try:
        import uvloop
        uvloop.install()
    except ImportError:
        pass

    asyncio.run(main())
