from bson import ObjectId
from bot.database.connection import samples_col
from bot.database.models import new_sample_doc


async def add_sample(plan: str, file_id: str, file_type: str, caption: str, added_by: int) -> str:
    doc = new_sample_doc(plan, file_id, file_type, caption, added_by)
    result = await samples_col.insert_one(doc)
    return str(result.inserted_id)


async def get_samples(plan: str) -> list[dict]:
    cursor = samples_col.find({"plan": plan}).sort("added_date", 1)
    return [doc async for doc in cursor]


async def delete_sample(sample_id: str) -> bool:
    result = await samples_col.delete_one({"_id": ObjectId(sample_id)})
    return result.deleted_count > 0
