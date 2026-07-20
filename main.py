import asyncio

from pyrogram import Client, idle

from bot.config import config, validate_and_report
from bot.utils.logger import logger
from bot.utils.plugin_loader import verify_plugins
from bot.database.connection import ensure_indexes, db
from bot.database.seed import seed_defaults
from bot.webserver import run_webserver


app = Client(
    "premium_content_bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
    # Dotted form is Pyrogram's documented convention for the plugins root.
    # (Handler registration for every @Client.on_message / on_callback_query
    # decorator in bot/plugins still happens here -- unchanged from before.)
    plugins=dict(root="bot.plugins"),
)


async def check_mongo_connection():
    """Fail fast and loudly if MongoDB isn't reachable, instead of hanging
    on the first real query with an opaque timeout deep in ensure_indexes()."""
    try:
        await asyncio.wait_for(db.command("ping"), timeout=10)
    except Exception as e:
        logger.error("MongoDB connection FAILED: %s", e)
        raise SystemExit(
            "Could not connect to MongoDB. Check MONGO_URI, network access rules, "
            "and IP allowlist (e.g. Atlas Network Access) before redeploying."
        )
    logger.info("MongoDB connected successfully.")


async def startup_tasks():
    await check_mongo_connection()

    logger.info("Ensuring MongoDB indexes...")
    await ensure_indexes()

    logger.info("Seeding default plans/settings (idempotent)...")
    await seed_defaults()

    logger.info("Database startup checks complete.")


async def main():
    problems = validate_and_report()
    if problems:
        raise SystemExit(
            "Startup aborted due to missing configuration:\n- " + "\n- ".join(problems) +
            "\n\nCopy .env.example to .env (or set these in Koyeb's environment "
            "variables panel) and redeploy."
        )

    # 1. Health-check server first -- Koyeb needs this bound quickly, and it
    #    must never be blocked by (or block) the bot's own startup.
    await run_webserver()
    logger.info("Health server started (listening on port %s).", config.PORT)

    # 2. Database checks + indexing + seeding.
    await startup_tasks()

    # 3. Pre-flight import every plugin file with full error visibility,
    #    BEFORE Pyrogram's own (much quieter) plugin loader runs inside
    #    app.start(). Any broken plugin is logged clearly here.
    succeeded, failed, failed_modules = verify_plugins("bot/plugins")
    if failed:
        logger.error(
            "%d plugin file(s) failed to import and will NOT provide working "
            "handlers: %s", failed, ", ".join(failed_modules),
        )
    if succeeded == 0:
        raise SystemExit("No plugins loaded successfully -- the bot has no handlers. Aborting.")

    # 4. Start the actual Telegram client. If credentials are wrong, this is
    #    where it will raise -- and we now surface that clearly instead of
    #    letting it crash the whole process silently.
    try:
        await app.start()
    except Exception:
        logger.exception("Bot FAILED to start / connect to Telegram.")
        raise

    me = await app.get_me()
    logger.info("Bot connected successfully: @%s (id=%s)", me.username, me.id)
    logger.info("Plugins loaded: %d/%d modules registered handlers.", succeeded, succeeded + failed)
    logger.info("Bot is now receiving live updates from Telegram (e.g. /start will respond).")

    # 5. Block here, dispatching updates, until a shutdown signal (SIGINT/
    #    SIGTERM) is received -- this is Pyrogram's own recommended
    #    long-running entrypoint and handles Koyeb's stop signal cleanly.
    await idle()

    logger.info("Shutdown signal received, stopping bot...")
    await app.stop()
    logger.info("Bot stopped cleanly.")


if __name__ == "__main__":
    try:
        import uvloop
        uvloop.install()
    except ImportError:
        pass

    asyncio.run(main())
