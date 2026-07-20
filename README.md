# Premium Content Selling Telegram Bot

A production-ready Telegram bot for selling subscription-based premium
content via one-time activation keys. Built with **Pyrogram**, **MongoDB
(Motor)**, and a modular plugin architecture. Deploys cleanly to **Koyeb**.

## Features

- 💎 Three fixed plans (₹199 / ₹299 / ₹799) with editable title/description/price
- 🎁 Admin-curated sample previews per plan (never exposes premium content)
- 🔓 Get More → QR code, payment details, contact admin, enter key
- 🔑 Cryptographically random, single-use activation keys with **atomic**
  MongoDB redemption (race-condition proof)
- 👑 Automatic subscription-status detection (`✅ Owned / 👑 Current Plan`)
- 📂 Paginated content feed (10 items/page, stable ordering, no duplicates)
- 🎥📷📁 Category browsing — exclusive to the ₹799 All Access plan
- 📢 Optional force-join channel enforcement
- 📋 Optional admin log channel for key redemptions, broadcasts, and new users
- 🛠 Fully button-based admin panel with `/cancel` to abort any multi-step flow
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
    │   ├── log_channel.py     # optional LOG_CHANNEL event forwarding
    │   ├── pagination.py
    │   └── logger.py
    └── plugins/
        ├── start.py, plans.py, activation.py, content_feed.py
        └── admin/
            ├── panel.py (includes /cancel), welcome.py, plans_admin.py,
            ├── samples_admin.py, content_admin.py, keys_admin.py,
            └── broadcast.py, statistics_admin.py, payment_settings.py, common.py
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
   the configured `ADMIN_IDS`) to open the admin panel.

## Expected Startup Log (healthy boot)

```
---- Environment variable check ----
API_ID: OK (...)
API_HASH: OK (xxxx****)
BOT_TOKEN: OK (1234****)
MONGO_URI: OK (mongodb+srv:***)
ADMIN_IDS: OK (1 admin(s) configured)
-------------------------------------
Health server started (listening on port 8000).
MongoDB connected successfully.
Ensuring MongoDB indexes...
Seeding default plans/settings (idempotent)...
Database startup checks complete.
---- Loading plugins from '/app/bot/plugins' ----
Loaded plugin: bot.plugins.activation
Loaded plugin: bot.plugins.content_feed
...
---- Plugin loading complete: 14 succeeded, 0 failed (of 14 files) ----
Bot connected successfully: @your_bot_username (id=123456789)
Plugins loaded: 14/14 modules registered handlers.
Bot is now receiving live updates from Telegram (e.g. /start will respond).
```

## Deploying to Koyeb

### Option A — Dockerfile (recommended)

1. Push this repo to GitHub.
2. In Koyeb: **Create App → GitHub → select repo**.
3. Koyeb detects the `Dockerfile` automatically.
4. Set **Environment Variables** (from `.env.example`):
   `API_ID`, `API_HASH`, `BOT_TOKEN`, `MONGO_URI`, `DB_NAME`, `ADMIN_IDS`,
   `LOG_CHANNEL` (optional), `FORCE_JOIN_CHANNEL` (optional), `PORT=8000`.
5. Set exposed port to `8000` and health-check path to `/health`.
6. Deploy.

### Option B — Buildpack (no Dockerfile)

1. Same GitHub setup, but choose **Buildpack** instead of Dockerfile.
2. Koyeb picks up `requirements.txt` and the `Procfile` (`web: python main.py`).
3. Set the same environment variables as above.

> **Note:** The Procfile declares `web:` (not `worker:`). Koyeb web services
> require this to correctly route the HTTP health check to your process and
> apply the right restart policy.

## Bug Fixes Applied (vs. previous version)

| # | What was fixed |
|---|----------------|
| 1 | `Procfile`: `worker:` → `web:` — Koyeb web services require the `web:` process type |
| 2 | `main.py`: added `in_memory=True` to `Client` — prevents session-loss restart loops on ephemeral Koyeb filesystem |
| 3 | `plugin_loader.py` / `main.py`: plugin path is now absolute (derived from `__file__`) — no longer CWD-sensitive |
| 4 | `main.py`: `ensure_indexes()` and `seed_defaults()` wrapped in `asyncio.wait_for` timeouts (30 s / 15 s) |
| 5 | `users.py`: `apply_activation` — `>=` → `>` rank comparison; same-plan re-activation no longer pollutes `previous_plans` |
| 6 | `plans_admin.py`: `plan_edit_menu_handler` — added `None` guard before accessing `plan['title']` |
| 7 | `keys.py`: `redeem_key` — revoked keys now return `"not_found"` instead of misleading `"used"` |
| 8 | `keys.py`: `create_keys` — catches `BulkWriteError` specifically; success path only extends with actually-inserted keys |
| 9 | `panel.py`: added `/cancel` command — admins can abort any multi-step flow without restarting the bot |
| 10 | `start.py`: `FORCE_JOIN_CHANNEL` is now actually enforced with a membership check + "I Joined" re-check button |
| 11 | `log_channel.py` (new): `LOG_CHANNEL` events now sent for `/start`, key redemptions, and broadcast completion |
| 12 | `statistics_admin.py`: added `parse_mode=ParseMode.MARKDOWN` so `**bold**` renders correctly |
| 13 | `content_feed.py`, `plans.py`: added `FloodWait` retry + 0.35 s inter-message delay on all media send loops |
| 14 | `users.py`: documented that subscription expiry is not implemented (keys have expiry; users do not) |
| 15 | `user_kb.py`: `content_nav_kb` — clamps `total_pages` to ≥ 1; prev/next share one row cleanly |

## Admin Workflow

- `/admin` → admin panel (use `/cancel` any time to abort a pending prompt)
- **Welcome Settings** — set welcome photo/message
- **Manage Plans** — edit title/description/price for each plan
- **Manage Samples** — upload preview media per plan
- **Upload Content** — add premium videos/photos/files
- **Activation Keys** — generate (1/5/10/50), view unused/used, bulk-delete unused
- **Payment Settings** — QR code, payment details text, contact-admin text
- **Broadcast** — message all users at once
- **Statistics** — live snapshot of users, subscribers, and keys

## Security Notes

- Activation keys use Python's `secrets` module (cryptographically secure).
- Key redemption is a single atomic `find_one_and_update` — race-condition proof.
- Subscription status is always read fresh from MongoDB — never cached.
- `/admin` and every admin callback is gated by `@admin_only` checked against `ADMIN_IDS`.
