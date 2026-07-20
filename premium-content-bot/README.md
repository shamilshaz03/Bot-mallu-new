# 🤖 Premium Content Selling Telegram Bot

A production-ready Telegram bot for selling premium digital content via a one-time activation key system. Built with **Pyrogram 2.x**, **Motor (async MongoDB)**, and deployed on **Koyeb**.

---

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Environment Variables](#environment-variables)
- [Deployment on Koyeb](#deployment-on-koyeb)
- [Admin Panel Guide](#admin-panel-guide)
- [User Flow](#user-flow)
- [Subscription Plans](#subscription-plans)
- [Activation Key System](#activation-key-system)
- [Content Management](#content-management)
- [Troubleshooting](#troubleshooting)

---

## ✨ Features

### User Features
- Clean, premium Telegram-native UI
- Browse three subscription plans with sample previews
- One-tap payment via QR code + payment details
- Single-use activation key redemption
- Instant content access after activation (no `/start` needed)
- Paginated content feed (10 items per page)
- Automatic subscription status display:
  - 👑 **Current Plan** — active plan
  - ✅ **Subscribed** — previously owned plan (access preserved)
  - ⬆️ **Upgrade** — higher tier available
- Category browsing (Videos / Photos / Files) for ₹799 plan only

### Admin Features
- Fully button-based admin panel — no slash commands for daily management
- Edit welcome photo and welcome message
- Manage plan titles, descriptions, and prices
- Upload content by selecting the target plan and category
- **📋 Content Library** — browse, edit captions, and delete existing content inline
- Manage sample content per plan (add / delete)
- Generate activation keys (1 / 5 / 10 / 50 at once)
- View unused and used keys
- Delete unused keys in bulk
- Broadcast messages to all users
- View live statistics
- Configure payment QR code, payment details, and contact admin link
- Force-join channel enforcement
- Maintenance mode

---

## 🏗 Architecture

```
Telegram ──► Pyrogram 2.x (plugin-based handler registration)
                   │
                   ├── Motor (async MongoDB Atlas)
                   ├── aiohttp (health server for Koyeb)
                   └── In-memory state store (FSM for multi-step flows)
```

**Key design decisions:**

- `in_memory=True` on the Pyrogram `Client` — no `.session` file written to the ephemeral Koyeb filesystem.
- Plugin modules are **never pre-imported** before `app.start()`. Pyrogram's own loader (`plugins=dict(root="bot.plugins")`) runs inside `app.start()` and owns all handler registration. Pre-importing populates `sys.modules` and silently breaks registration.
- Motor `AsyncIOMotorClient` is created once at module import — this is correct per Motor docs for async applications.
- `state_store` is a process-local in-memory dict — intentional for single-process Koyeb deployments.
- Atomic MongoDB `find_one_and_update` with `status: "unused"` filter prevents any race condition on key redemption, even under concurrent requests.

---

## 📁 Project Structure

```
premium-content-bot/
├── Procfile                        # web: python main.py
├── Dockerfile
├── requirements.txt
├── .env.example
├── main.py                         # Startup: health server → DB → Pyrogram client
└── bot/
    ├── config.py                   # All env vars + PLAN_RANK mapping
    ├── strings.py                  # All user-facing message templates
    ├── webserver.py                # aiohttp health check server
    ├── database/
    │   ├── connection.py           # Motor client + index creation
    │   ├── models.py               # Document shapes + DEFAULT_PLANS/SETTINGS
    │   ├── seed.py                 # Seeds plans/settings on first run
    │   ├── users.py                # User CRUD + apply_activation + owned_plans
    │   ├── keys.py                 # Key creation + atomic redemption
    │   ├── plans.py                # Plan CRUD
    │   ├── contents.py             # Content CRUD + paginated fetch
    │   ├── samples.py              # Sample CRUD
    │   ├── settings.py             # Key-value settings store
    │   └── statistics.py           # Stats report builder
    ├── keyboards/
    │   ├── user_kb.py              # All user-facing inline keyboards
    │   └── admin_kb.py             # All admin inline keyboards
    ├── utils/
    │   ├── decorators.py           # @admin_only, state_store (FSM)
    │   ├── log_channel.py          # send_log() helper for LOG_CHANNEL
    │   ├── pagination.py           # total_pages() helper
    │   ├── key_generator.py        # Cryptographically random key generator
    │   └── logger.py               # Structured logger
    └── plugins/
        ├── start.py                # /start, force-join check, contact admin
        ├── activation.py           # Key redemption flow
        ├── plans.py                # Plan list, plan view, samples, get-more
        ├── content_feed.py         # Paginated feed, category browsing
        └── admin/
            ├── panel.py            # /admin, admin:home, /cancel
            ├── welcome.py          # Edit welcome photo/message
            ├── plans_admin.py      # Edit plan fields
            ├── content_admin.py    # Upload + Content Library (edit/delete)
            ├── samples_admin.py    # Manage sample content
            ├── keys_admin.py       # Generate/view/delete keys
            ├── broadcast.py        # Broadcast to all users
            ├── statistics_admin.py # Statistics report
            ├── payment_settings.py # QR code + payment details + contact
            └── common.py           # Shared admin helpers
```

---

## ⚙️ Setup & Installation

### Prerequisites

- Python 3.11+
- MongoDB Atlas account (free tier is fine)
- Telegram Bot Token from [@BotFather](https://t.me/BotFather)
- Telegram API credentials from [my.telegram.org](https://my.telegram.org)

### Local Development

```bash
# 1. Clone the repository
git clone https://github.com/yourname/premium-content-bot.git
cd premium-content-bot

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and fill in environment variables
cp .env.example .env
# Edit .env with your values

# 5. Run the bot
python main.py
```

---

## 🔑 Environment Variables

Copy `.env.example` to `.env` and fill in every value.

| Variable | Required | Description |
|---|---|---|
| `BOT_TOKEN` | ✅ | Bot token from @BotFather |
| `API_ID` | ✅ | Telegram API ID from my.telegram.org |
| `API_HASH` | ✅ | Telegram API hash from my.telegram.org |
| `MONGO_URI` | ✅ | MongoDB connection string (Atlas recommended) |
| `ADMIN_IDS` | ✅ | Comma-separated Telegram user IDs, e.g. `123456,789012` |
| `PORT` | ✅ | Port for health server (Koyeb sets this automatically) |
| `LOG_CHANNEL` | ❌ | Telegram channel/group ID for operational logs (optional) |
| `FORCE_JOIN_CHANNEL` | ❌ | Channel username (e.g. `@mychannel`) users must join before using the bot |

### Example `.env`

```env
BOT_TOKEN=7123456789:AAF...
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890
MONGO_URI=mongodb+srv://user:password@cluster.mongodb.net/premiumbot?retryWrites=true&w=majority
ADMIN_IDS=123456789,987654321
PORT=8080
LOG_CHANNEL=-1001234567890
FORCE_JOIN_CHANNEL=@mychannelname
```

> ⚠️ **MongoDB Atlas Network Access**: Set IP access to `0.0.0.0/0` (allow all) or add Koyeb's IP ranges. A restricted network is the most common reason for connection failures on Koyeb.

---

## 🚀 Deployment on Koyeb

### Step 1 — Create a Koyeb service

1. Go to [app.koyeb.com](https://app.koyeb.com) and create a new **Web Service**.
2. Connect your GitHub repository (or upload the zip via Koyeb CLI).
3. Set **Build command**: `pip install -r requirements.txt`
4. Set **Run command**: `python main.py` (or leave blank — Koyeb reads `Procfile`).
5. Set **Port**: `8080` (must match your `PORT` env var).
6. Set **Health check path**: `/health`

### Step 2 — Set environment variables

In the Koyeb dashboard under **Environment**, add all variables from the table above.

### Step 3 — Deploy

Click **Deploy**. Watch the logs — you should see:

```
Health server started on port 8080.
MongoDB connected successfully.
Ensuring MongoDB indexes...
Database startup complete.
Starting Pyrogram client (loading plugins)...
Bot connected: @your_bot_name (id=...)
Handlers registered: 42
Bot is now receiving live updates from Telegram.
```

If you see `Handlers registered: 0` the bot will ignore all messages. This means a plugin module was imported before `app.start()`. Do **not** add any `import bot.plugins.*` statements anywhere in the startup path.

---

## 🛠 Admin Panel Guide

Send `/admin` to the bot in a private chat (admin accounts only).

### 🖼 Welcome Settings
Upload or change the welcome photo and welcome message shown to all users on `/start`.

### 💳 Manage Plans
Edit each plan's **title**, **description**, and **price** individually.

### 🎁 Manage Samples
Add or remove sample content (photo/video/document + caption) for each plan. Samples are shown to **non-subscribers** only — never premium content.

### 📤 Upload Content
Select a plan → (for ₹799, select a category) → send the media with a caption. The item is immediately indexed and available to subscribers.

### 📋 Content Library
Browse all uploaded content for any plan, page by page. Each item shows:
- **✏️ Edit Caption** — prompts for new caption text, updates instantly.
- **🗑 Delete** — asks for confirmation inline, then removes the item from the database.

No slash commands required for any of this.

### 🔑 Activation Keys
- **Generate Keys** — select plan → select quantity (1 / 5 / 10 / 50) → keys are generated and displayed.
- **View Unused Keys** — list all unredeemed keys.
- **View Used Keys** — list all redeemed keys with user ID and date.
- **Delete Unused Keys** — bulk-delete all unredeemed keys for a plan.

### 📢 Broadcast
Send any message or media to all registered users. Handles FloodWait automatically with retry logic.

### 📊 Statistics
Live report showing: total users, active subscribers, per-plan subscriber counts, total content items, total keys (unused / used).

### 💰 Payment Settings
- Upload / update the payment **QR code** image.
- Set **payment details** text (UPI ID, bank details, etc.).
- Set **contact admin** link shown in the contact button.

---

## 👤 User Flow

```
/start
  └─► Welcome photo + message
        └─► [💎 Plans]
              └─► Plan list (with subscription status labels)
                    └─► [Plan card] → samples + plan details
                          ├─► [📂 Browse Content]  ← shown only if subscribed
                          └─► [🔓 Get More]
                                ├─► QR code + payment details
                                ├─► [📞 Contact Admin]
                                └─► [🔑 Enter Activation Key]
                                      └─► Send key → validated atomically
                                            └─► ✅ Success + [📂 View My Content Now]
                                                  └─► Paginated content feed
```

---

## 💳 Subscription Plans

| Plan | Price | Content | Category Browsing |
|---|---|---|---|
| Starter | ₹199 | Mixed feed | ❌ |
| Plus | ₹299 | Mixed feed | ❌ |
| All Access | ₹799 | Full library | ✅ Videos / Photos / Files |

### Upgrade Logic

When a user upgrades to a higher plan, their previous plan access is **preserved** — they can still browse content from their old plan. `previous_plans` in MongoDB tracks all owned plans.

**Example:** A ₹199 subscriber who upgrades to ₹299 sees:

| Plan | Label |
|---|---|
| ₹199 | ✅ Subscribed (still accessible) |
| ₹299 | 👑 Current Plan (active) |
| ₹799 | ⬆️ Upgrade (available) |

---

## 🔐 Activation Key System

### Key Format

```
199-K3F9-QP2M
299-AB3C-XY7Z
799-MN5P-QR2T
```

Plan prefix + two 4-character blocks. Characters from `A-Z 2-9` (excludes `O`, `0`, `I`, `1` to reduce user typos).

### Security

- Generated with Python's `secrets` module (cryptographically random).
- Unique index on `key` field in MongoDB prevents collisions.
- Redemption uses atomic `find_one_and_update` with `{status: "unused"}` filter — even simultaneous requests from two users cannot both succeed.
- Used keys have `status: "used"` and are permanently blocked.
- Revoked keys return the same error as invalid keys (no information leakage).

### Admin Workflow

1. User pays via QR / UPI.
2. Admin verifies payment manually.
3. Admin opens `/admin` → Activation Keys → Generate Keys → select plan → select quantity.
4. Admin sends the generated key to the user.
5. User taps **Enter Activation Key**, sends the key.
6. Bot validates atomically, activates the plan, and immediately shows the content feed.

---

## 📦 Content Management

### MongoDB Collections

| Collection | Purpose |
|---|---|
| `users` | User profiles + subscription state |
| `keys` | Activation keys + redemption status |
| `plans` | Plan metadata (title, description, price) |
| `contents` | Premium content items |
| `samples` | Sample content (pre-purchase previews) |
| `settings` | Bot configuration (welcome, payment, etc.) |

### Indexes

```python
# contents — optimized for paginated feed queries
contents: [plan + category + upload_date]
contents: [file_type + upload_date]

# keys — fast lookup by key string
keys: [key (unique)]
keys: [status]
keys: [plan + status]

# users — fast lookup by user_id
users: [user_id (unique)]
```

---

## 🐛 Troubleshooting

### Bot starts but ignores all messages

**Cause:** A plugin module was imported before `app.start()`.  
**Fix:** Never add `import bot.plugins.*` anywhere before `await app.start()`. Pyrogram's own loader handles registration inside `start()`.

Check the startup log for:
```
Handlers registered: 0   ← broken
Handlers registered: 42  ← correct
```

---

### `MongoServerSelectionError` on startup

**Cause:** Atlas Network Access is blocking Koyeb's IP.  
**Fix:** In Atlas → Network Access → Add IP Address → `0.0.0.0/0`.

---

### FloodWait errors in logs

Normal for large broadcasts or when sending many samples quickly. The bot retries automatically with the wait time Telegram specifies + 1 second buffer. No action needed.

---

### `/start` shows no response after redeployment

Koyeb takes 30–60 seconds to route traffic to the new instance. Wait for the health check to pass (green in Koyeb dashboard) before testing. Watch the deployment logs for `Bot is now receiving live updates`.

---

### Admin panel shows "Plan not found"

The database was not seeded. This can happen if the seed step timed out on first run. Check Atlas cluster health and your `MONGO_URI`. Send `/admin` again — the panel loads fresh data on every open.

---

## 📄 License

MIT License — free to use, modify, and deploy.
