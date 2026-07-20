"""
Single Motor client shared across the whole app.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from bot.config import config

_client = AsyncIOMotorClient(config.MONGO_URI)
db = _client[config.DB_NAME]

# Collections (as specified in the requirements doc)
users_col = db["users"]
plans_col = db["plans"]
contents_col = db["contents"]
samples_col = db["samples"]
keys_col = db["activation_keys"]
settings_col = db["settings"]
statistics_col = db["statistics"]


async def ensure_indexes():
    """Create all indexes needed for fast, optimized queries. Safe to call on every startup."""
    await users_col.create_index("user_id", unique=True)
    await users_col.create_index("current_plan")

    await plans_col.create_index("plan_id", unique=True)

    await contents_col.create_index([("plan", 1), ("category", 1), ("upload_date", -1)])
    await contents_col.create_index("file_id")
    await contents_col.create_index("caption")

    await samples_col.create_index("plan")

    await keys_col.create_index("key", unique=True)
    await keys_col.create_index([("plan", 1), ("status", 1)])
    await keys_col.create_index("used_by")

    await settings_col.create_index("key", unique=True)
