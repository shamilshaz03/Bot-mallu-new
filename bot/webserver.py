"""
Koyeb (and most PaaS hosts) expects a web service to bind to $PORT.
This tiny aiohttp server exists purely for health checks — the actual
work happens in the Pyrogram client running in the same event loop.

The /health endpoint also reports bot connection status so you can
diagnose Telegram issues without needing access to runtime logs.
"""
from aiohttp import web
from bot.config import config

# Startup state written by main.py before/after app.start()
startup_status = {
    "stage": "starting",      # starting | db_ok | bot_connected | failed
    "bot_username": None,
    "handlers": None,
    "error": None,
}


async def health(request):
    s = startup_status
    lines = [
        f"stage: {s['stage']}",
        f"bot: @{s['bot_username']}" if s["bot_username"] else "bot: not connected yet",
        f"handlers: {s['handlers']}" if s["handlers"] is not None else "handlers: unknown",
        f"error: {s['error']}" if s["error"] else "",
    ]
    body = "\n".join(l for l in lines if l)

    status = 200 if s["stage"] == "bot_connected" else 503
    return web.Response(text=body, status=status)


def build_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    return app


async def run_webserver():
    app = build_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", config.PORT)
    await site.start()
