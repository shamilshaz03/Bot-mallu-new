import asyncio
from pyrogram import Client, idle
from bot.config import config, validate_and_report
from bot.utils.logger import logger
from bot.database.connection import ensure_indexes, db
from bot.database.seed import seed_defaults
from bot.webserver import run_webserver

# NOTE: Do NOT pre-import plugin modules here or in any helper called before
# app.start(). Doing so populates sys.modules before Pyrogram's own loader
# runs inside app.start(), causing importlib.import_module() inside Pyrogram
# to return cached modules without ever calling app.add_handler() — leaving
# zero handlers registered and the bot silently ignoring all messages.
app = Client(
    "premium_content_bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
    plugins=dict(root="bot.plugins"),
    # BUG-2 FIX: in_memory=True prevents a .session file being written to
    # the ephemeral Koyeb filesystem. Bots re-auth via bot_token every start;
    # a stale session file causes auth-failure restart loops.
    in_memory=True,
)


async def check_mongo():
    try:
        await asyncio.wait_for(db.command("ping"), timeout=10)
    except Exception as e:
        raise SystemExit(f"MongoDB connection FAILED: {e}\nCheck MONGO_URI and Atlas Network Access rules.")
    logger.info("MongoDB connected successfully.")


async def startup_tasks():
    await check_mongo()
    # BUG-4 FIX: timeouts prevent a slow Atlas cluster from hanging the
    # process indefinitely after the health server has already bound its port.
    logger.info("Ensuring MongoDB indexes...")
    try:
        await asyncio.wait_for(ensure_indexes(), timeout=30)
    except asyncio.TimeoutError:
        raise SystemExit("ensure_indexes() timed out (30 s). Check Atlas cluster health.")

    logger.info("Seeding default plans/settings...")
    try:
        await asyncio.wait_for(seed_defaults(), timeout=15)
    except asyncio.TimeoutError:
        raise SystemExit("seed_defaults() timed out (15 s). Check Atlas cluster health.")
    logger.info("Database startup complete.")


async def main():
    problems = validate_and_report()
    if problems:
        raise SystemExit(
            "Startup aborted — missing configuration:\n- " + "\n- ".join(problems) +
            "\n\nSet these in Koyeb's environment variables panel and redeploy."
        )

    # 1. Health server first — Koyeb needs this bound quickly.
    await run_webserver()
    logger.info("Health server started on port %s.", config.PORT)

    # 2. Database (with timeouts).
    await startup_tasks()

    # 3. Start Telegram client — Pyrogram's plugin loader runs inside here.
    logger.info("Starting Pyrogram client (loading plugins)...")
    try:
        await app.start()
    except Exception:
        logger.exception("Bot FAILED to connect to Telegram.")
        raise

    me = await app.get_me()
    handler_count = sum(len(g) for g in app.dispatcher.groups.values()) \
        if hasattr(app, "dispatcher") and hasattr(app.dispatcher, "groups") else "?"
    logger.info("Bot connected: @%s (id=%s)", me.username, me.id)
    logger.info("Handlers registered: %s", handler_count)
    logger.info("Bot is now receiving live updates from Telegram.")

    await idle()

    logger.info("Shutdown signal received — stopping.")
    await app.stop()
    logger.info("Bot stopped cleanly.")


if __name__ == "__main__":
    try:
        import uvloop
        uvloop.install()
    except ImportError:
        pass
    asyncio.run(main())
