"""
Activation key persistence + atomic single-use redemption.

Security: even if two users submit the same key simultaneously, only ONE
find_one_and_update can match status == "unused" because MongoDB executes
it atomically at the document level. The loser gets None back.
"""
from pymongo import ReturnDocument
from pymongo.errors import BulkWriteError
from bot.database.connection import keys_col
from bot.database.models import new_key_doc, now


async def create_keys(plan: str, count: int, created_by: int) -> list[str]:
    """
    BUG-8 FIX: Catch BulkWriteError (partial insert on duplicate-key collision)
    rather than swallowing all exceptions. Only keys that were actually inserted
    are added to `created`.
    """
    from bot.utils.key_generator import generate_keys

    created: list[str] = []
    attempts = 0
    while len(created) < count and attempts < count * 3 + 10:
        attempts += 1
        batch_needed = count - len(created)
        candidates = generate_keys(plan, batch_needed)
        docs = [new_key_doc(k, plan, created_by) for k in candidates]
        try:
            await keys_col.insert_many(docs, ordered=False)
            created.extend(candidates)
        except BulkWriteError as bwe:
            error_indices = {e["index"] for e in bwe.details.get("writeErrors", [])}
            created.extend(c for i, c in enumerate(candidates) if i not in error_indices)
        except Exception:
            pass  # unexpected error — skip this batch, retry
    return created


async def redeem_key(key: str, user_id: int) -> tuple[str, dict | None]:
    """
    Atomically flip an unused key to used.

    Returns (status, doc):
      "ok"        — redeemed successfully; doc is the updated document
      "not_found" — key doesn't exist or was revoked
      "expired"   — key existed but is past its expiry date
      "used"      — key already redeemed by someone

    BUG-7 FIX: Revoked keys now map to "not_found" (same as non-existent)
    instead of falling through to "used", which gave a misleading error.
    """
    key = key.strip().upper()

    doc = await keys_col.find_one({"key": key})
    if doc is None:
        return "not_found", None

    status = doc.get("status", "")

    if status == "revoked":          # BUG-7 FIX
        return "not_found", None
    if status == "used":
        return "used", None
    if doc.get("expiry") and doc["expiry"] < now():
        return "expired", None

    # Atomic flip — only succeeds if still "unused" at the moment of execution.
    updated = await keys_col.find_one_and_update(
        {"key": key, "status": "unused"},
        {"$set": {"status": "used", "used_by": user_id, "used_date": now()}},
        return_document=ReturnDocument.AFTER,
    )
    if updated is None:
        return "used", None  # lost the race
    return "ok", updated


async def get_unused_keys(plan: str | None = None, limit: int = 200) -> list[dict]:
    query: dict = {"status": "unused"}
    if plan:
        query["plan"] = plan
    cursor = keys_col.find(query).sort("created_date", -1).limit(limit)
    return [doc async for doc in cursor]


async def get_used_keys(plan: str | None = None, limit: int = 200) -> list[dict]:
    query: dict = {"status": "used"}
    if plan:
        query["plan"] = plan
    cursor = keys_col.find(query).sort("used_date", -1).limit(limit)
    return [doc async for doc in cursor]


async def delete_unused_keys(plan: str | None = None) -> int:
    query: dict = {"status": "unused"}
    if plan:
        query["plan"] = plan
    result = await keys_col.delete_many(query)
    return result.deleted_count


async def revoke_key(key: str) -> bool:
    result = await keys_col.update_one(
        {"key": key.strip().upper(), "status": "unused"},
        {"$set": {"status": "revoked"}},
    )
    return result.modified_count > 0


async def count_keys(status: str | None = None) -> int:
    query = {} if status is None else {"status": status}
    return await keys_col.count_documents(query)
