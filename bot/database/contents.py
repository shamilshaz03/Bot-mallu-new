from bot.database.connection import contents_col
from bot.database.models import new_content_doc
from bot.config import config


async def add_content(
    plan: str,
    category: str | None,
    file_id: str,
    file_type: str,
    caption: str,
    preview_file_id: str | None,
    preview_caption: str | None,
    thumbnail: str | None,
    uploaded_by: int,
) -> str:
    doc = new_content_doc(
        plan, category, file_id, file_type, caption,
        preview_file_id, preview_caption, thumbnail, uploaded_by,
    )
    result = await contents_col.insert_one(doc)
    return str(result.inserted_id)


async def get_content_page(plan: str, page: int, category: str | None = None) -> tuple[list[dict], int]:
    """Returns (items, total_count) for stable, indexed, fast pagination."""
    query: dict = {"plan": plan}
    if category:
        query["category"] = category

    total = await contents_col.count_documents(query)
    skip = max(page - 1, 0) * config.ITEMS_PER_PAGE
    cursor = (
        contents_col.find(query)
        .sort([("upload_date", -1), ("_id", -1)])  # stable ordering, no duplicates across pages
        .skip(skip)
        .limit(config.ITEMS_PER_PAGE)
    )
    items = [doc async for doc in cursor]
    return items, total


async def delete_content(content_id) -> bool:
    from bson import ObjectId
    result = await contents_col.delete_one({"_id": ObjectId(content_id)})
    return result.deleted_count > 0


async def edit_content_caption(content_id, new_caption: str) -> bool:
    from bson import ObjectId
    result = await contents_col.update_one(
        {"_id": ObjectId(content_id)}, {"$set": {"caption": new_caption}}
    )
    return result.modified_count > 0


async def count_content(plan: str | None = None) -> int:
    query = {} if plan is None else {"plan": plan}
    return await contents_col.count_documents(query)
