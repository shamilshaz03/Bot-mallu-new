# Premium Content Selling Telegram Bot

A production-ready Telegram bot for selling subscription-based premium
content via one-time activation keys. Built with **Pyrogram**, **MongoDB
(Motor)**, and a modular plugin architecture. Deploys cleanly to **Koyeb**.

This is **not** a movie/auto-filter bot — it's a premium content
subscription platform with three fixed plans (₹199 / ₹299 / ₹799),
sample previews, manual payment + activation keys, and an all-button
admin panel.

## Features

- 💎 Three fixed plans, each with editable title/description/price
- 🎁 Admin-curated sample previews per plan (never exposes premium content)
- 🔓 Get More → QR code, payment details, contact admin, enter key
- 🔑 Cryptographically random, single-use activation keys with **atomic**
  MongoDB redemption (race-condition proof — a key can only ever be used once)
- 👑 Automatic subscription-status detection on every `/start`
  (✅ Subscribed / ⬆ Upgrade / 👑 Current Plan), upgrade path preserves
  all previously purchased access
- 📂 Paginated content feed (10 items/page, stable ordering, no duplicates)
- 🎥📷📁 Category browsing — exclusive to the ₹799 All Access plan
- 🛠 Fully button-based admin panel: welcome settings, plan editing,
  sample management, content upload/edit/delete, key generation &
  management, broadcast, statistics, payment/QR/contact settings
- ⚡ Async throughout, optimized MongoDB indexes, structured logging

## Project Structure

```
premium-content-bot/
├── main.py                  # Entrypoint (Pyrogram client + health server)
├── requirements.txt
├── Dockerfile
├── Procfile
├── .env.example
└── bot/
    ├── config.py             # All env-driven configuration
    ├── strings.py            # User-facing text
    ├── webserver.py          # Koyeb health-check endpoint
    ├── database/
    │   ├── connection.py      # Motor client + index creation
    │   ├── models.py          # Document shapes + defaults
    │   ├── seed.py             # Idempotent default plan/settings seeding
    │   ├── users.py, plans.py, keys.py, contents.py, samples.py,
    │   └── settings.py, statistics.py
    ├── keyboards/
    │   ├── user_kb.py
    │   └── admin_kb.py
    ├── utils/
    │   ├── key_generator.py   # secrets-based key generation
    │   ├── decorators.py      # admin_only + in-memory FSM state store
    │   ├── pagination.py
    │   └── logger.py
    └── plugins/
        ├── start.py, plans.py, activation.py, content_feed.py
        └── admin/
            ├── panel.py, welcome.py, plans_admin.py, samples_admin.py,
            ├── content_admin.py, keys_admin.py, broadcast.py,
            └── statistics_admin.py, payment_settings.py, common.py
```

## Local Setup

1. **Get Telegram API credentials**
   - `API_ID` / `API_HASH` from https://my.telegram.org
   - `BOT_TOKEN` from [@BotFather](https://t.me/BotFather)

2. **Get a MongoDB connection string**
   - Free tier works fine: https://www.mongodb.com/cloud/atlas

3. **Configure environment**
   ```bash
   cp .env.example .env
   # edit .env with your values, including ADMIN_IDS (your Telegram user ID)
   ```

4. **Install & run**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python main.py
   ```

5. Open your bot in Telegram, send `/start`, and send `/admin` (as one of
   the configured `ADMIN_IDS`) to open the admin panel and start
   configuring plans, samples, content, and payment details.

## Startup Audit Log (fixed issues)

If you previously hit **"bot deploys, health check passes, but `/start`
never responds"** or **`ModuleNotFoundError: No module named 'pyrogram'`**,
those were caused by:

1. **`requirements.txt` only pinned `motor`, not `pymongo`.** pip's
   resolver had to guess a `pymongo` version, hit a conflict with
   `motor==3.5.1`'s constraints, and aborted the *entire* install —
   including `pyrogram` — before anything got installed. Fixed by
   pinning a verified-compatible pair: `motor==3.6.0` + `pymongo==4.9.2`.
2. **No MongoDB connectivity check before use.** A bad/unreachable
   `MONGO_URI` would hang or fail deep inside index creation with no
   clear log line. `main.py` now does an explicit `db.command("ping")`
   with a 10s timeout and a clear error message before anything else runs.
3. **No confirmation the bot actually connected to Telegram.** `app.start()`
   was never wrapped in error handling, and there was no `get_me()` call to
   prove the bot token/connection actually worked. Both are now explicit
   and logged.
4. **Plugin import failures could go unnoticed.** Pyrogram's built-in
   plugin loader only warns and moves on. `main.py` now pre-imports every
   file under `bot/plugins` itself via `bot/utils/plugin_loader.py` and
   logs a clear success/failure line (with full traceback on failure) for
   each one before the bot starts.
5. **`asyncio.Event().wait()` replaced with Pyrogram's `idle()`**, which is
   the library's documented long-running entrypoint and handles
   SIGINT/SIGTERM (Koyeb's stop/restart signal) cleanly instead of an
   abrupt kill.
6. **Startup order fixed** so the health-check web server binds to `$PORT`
   *first* and independently of Mongo/bot startup, then Mongo checks run,
   then plugins are verified, then the bot connects — with a clear log
   line at each stage.

Expected log sequence on a healthy boot:

```
---- Environment variable check ----
API_ID: OK (...)
...
Health server started (listening on port 8000).
MongoDB connected successfully.
Ensuring MongoDB indexes...
Seeding default plans/settings (idempotent)...
---- Loading plugins from 'bot/plugins' ----
Loaded plugin: bot.plugins.start
...
---- Plugin loading complete: 21 succeeded, 0 failed (of 21 files) ----
Bot connected successfully: @your_bot_username (id=123456789)
Plugins loaded: 21/21 modules registered handlers.
Bot is now receiving live updates from Telegram (e.g. /start will respond).
```

## Python Version

This project targets **Python 3.10** (see `.python-version`, used by
Koyeb's buildpack) and the `Dockerfile` base image is pinned to
`python:3.10-slim` to match — keeping the buildpack and Docker deploy
paths consistent and avoiding compiled-wheel mismatches (e.g. `tgcrypto`).

## Deploying to Koyeb


### Option A — Dockerfile (recommended)

1. Push this repo to GitHub.
2. In Koyeb: **Create App → GitHub → select this repo**.
3. Koyeb will detect the `Dockerfile` automatically.
4. Set **Environment Variables** (from `.env.example`):
   `API_ID`, `API_HASH`, `BOT_TOKEN`, `MONGO_URI`, `DB_NAME`, `ADMIN_IDS`,
   `LOG_CHANNEL` (optional), `PORT=8000`.
5. Set the exposed port to `8000` and health-check path to `/health`.
6. Deploy. Koyeb will keep the process alive; the bundled aiohttp server
   satisfies Koyeb's health checks while Pyrogram handles bot updates in
   the same process.

### Option B — Buildpack (no Dockerfile)

1. Same GitHub setup, but choose **Buildpack** instead of Dockerfile.
2. Koyeb will pick up `requirements.txt` and the `Procfile` automatically
   (`worker: python main.py`).
3. Set the same environment variables as above.

## Admin Workflow (all in-app, no code edits needed)

- `/admin` → **Welcome Settings** to set the welcome photo/message
- **Manage Plans** to set title/description/price for each of the 3 plans
- **Manage Samples** to upload preview media per plan
- **Upload Content** to add premium videos/photos/files (choose
  plan, and category if ₹799)
- **Activation Keys** → Generate Keys (pick plan + count: 1/5/10/50),
  view unused/used keys, or bulk-delete unused keys
- **Payment Settings** to set the QR code, payment details text, and
  contact-admin text
- **Broadcast** to message all users at once
- **Statistics** for a live snapshot of users, subscribers, and keys

## Security Notes

- Activation keys are generated with Python's `secrets` module
  (cryptographically secure), never `random`.
- Key redemption uses a single atomic `find_one_and_update` — under a
  race between two users submitting the same key simultaneously, only
  one can ever succeed; MongoDB guarantees this at the document level.
- Subscription status is always read fresh from MongoDB — never cached
  or trusted from client input.
- `/admin` and every admin callback is gated by an `admin_only`
  decorator checked against `ADMIN_IDS` from the environment.

## Extending

The plugin system means new features are just new files dropped into
`bot/plugins/` or `bot/plugins/admin/` — Pyrogram auto-loads them at
startup, so nothing needs to be wired up manually in `main.py`.
