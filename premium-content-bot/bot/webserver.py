"""
Koyeb (and most PaaS hosts) expects a web service to bind to $PORT.
This tiny aiohttp server exists purely for health checks — the actual
work happens in the Pyrogram client running in the same event loop.
"""
from aiohttp import web
from bot.config import config


async def health(request):
    return web.Response(text="OK")


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
