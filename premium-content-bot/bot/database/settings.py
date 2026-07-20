from bot.database.connection import settings_col


async def get_setting(key: str):
    doc = await settings_col.find_one({"key": key})
    return doc["value"] if doc else None


async def set_setting(key: str, value) -> None:
    await settings_col.update_one({"key": key}, {"$set": {"value": value}}, upsert=True)


async def get_all_settings() -> dict:
    cursor = settings_col.find({})
    return {doc["key"]: doc["value"] async for doc in cursor}
