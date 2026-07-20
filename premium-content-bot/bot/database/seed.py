"""
Seeds default plans and settings on first run only (idempotent — never
overwrites existing admin edits).
"""
from bot.database.connection import plans_col, settings_col
from bot.database.models import DEFAULT_PLANS, DEFAULT_SETTINGS


async def seed_defaults():
    for plan in DEFAULT_PLANS:
        await plans_col.update_one(
            {"plan_id": plan["plan_id"]},
            {"$setOnInsert": plan},
            upsert=True,
        )

    for setting in DEFAULT_SETTINGS:
        await settings_col.update_one(
            {"key": setting["key"]},
            {"$setOnInsert": setting},
            upsert=True,
        )
