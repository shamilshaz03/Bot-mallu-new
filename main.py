import asyncio
from pathlib import Path

from pyrogram import Client, idle

from bot.config import config, validate_and_report
from bot.utils.logger import logger
from bot.utils.plugin_loader import verify_plugins
from bot.database.connection import ensure_indexes, db
from bot.database.seed import seed_defaults
from bot.webserver import run_webserver

# Resolve the plugins directory relative to this file, not CWD.
# This is robust regardless of where the process is launched from.
PLUGINS_ROOT = Path(__file__).parent / "bot" / "plugins"

app = Client(
    "premium_content_bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
    # Dotted form is Pyrogram's documented convention for the plugins root.
    plugins=dict(root="bot.plugins"),
    # BUG-2 FIX: Do not write a session file on the ephemeral Koyeb
    # filesystem. Bots authenticate via bot_token on every start, so an
    # on-disk session adds no value and causes auth-failure restart loops
    # when the container is recycled between deploys.
    in_memory=True,
)


async def check_mongo_connection():
    """Fail fast and loudly if MongoDB isn't reachable."""
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

    # BUG-4 FIX: Wrap index creation and seeding in timeouts so a slow
    # Atlas cluster can't hang the process indefinitely after the health
    # server has already bound its port (which would leave Koyeb showing
    # Healthy while the bot never actually starts).
    logger.info("Ensuring MongoDB indexes...")
    try:
        await asyncio.wait_for(ensure_indexes(), timeout=30)
    except asyncio.TimeoutError:
        raise SystemExit(
            "ensure_indexes() timed out after 30 s. "
            "Check MongoDB Atlas cluster health and network latency."
        )

    logger.info("Seeding default plans/settings (idempotent)...")
    try:
        await asyncio.wait_for(seed_defaults(), timeout=15)
    except asyncio.TimeoutError:
        raise SystemExit(
            "seed_defaults() timed out after 15 s. "
            "Check MongoDB Atlas cluster health and network latency."
        )

    logger.info("Database startup checks complete.")


async def main():
    problems = validate_and_report()
    if problems:
        raise SystemExit(
            "Startup aborted due to missing configuration:\n- " + "\n- ".join(problems) +
            "\n\nCopy .env.example to .env (or set these in Koyeb's environment "
            "variables panel) and redeploy."
        )

    # 1. Health-check server first — Koyeb needs this bound quickly.
    await run_webserver()
    logger.info("Health server started (listening on port %s).", config.PORT)

    # 2. Database checks + indexing + seeding (with timeouts — BUG-4).
    await startup_tasks()

    # 3. Pre-flight import every plugin file with full error visibility,
    #    BEFORE Pyrogram's own (much quieter) plugin loader runs inside
    #    app.start(). Any broken plugin is logged clearly here.
    #    BUG-3 FIX: Pass absolute path so verify_plugins works regardless of CWD.
    succeeded, failed, failed_modules = verify_plugins(str(PLUGINS_ROOT))
    if failed:
        logger.error(
            "%d plugin file(s) failed to import and will NOT provide working "
            "handlers: %s", failed, ", ".join(failed_modules),
        )
    if succeeded == 0:
        raise SystemExit("No plugins loaded successfully — the bot has no handlers. Aborting.")

    # 4. Start the actual Telegram client.
    try:
        await app.start()
    except Exception:
        logger.exception("Bot FAILED to start / connect to Telegram.")
        raise

    me = await app.get_me()
    logger.info("Bot connected successfully: @%s (id=%s)", me.username, me.id)
    logger.info("Plugins loaded: %d/%d modules registered handlers.", succeeded, succeeded + failed)
    logger.info("Bot is now receiving live updates from Telegram (e.g. /start will respond).")

    # 5. Block here, dispatching updates, until SIGINT/SIGTERM.
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
