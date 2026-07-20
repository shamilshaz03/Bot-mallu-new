"""
Activation key persistence + the critical atomic redemption logic.

Security guarantee: even under a race (two users submitting the same key
at the same instant), only ONE find_one_and_update can ever match a key
whose status is still "unused", because MongoDB executes the operation
atomically at the document level. The loser simply gets `None` back.
"""
from pymongo import ReturnDocument
from pymongo.errors import BulkWriteError
from bot.database.connection import keys_col
from bot.database.models import new_key_doc, now


async def create_keys(plan: str, count: int, created_by: int) -> list[str]:
    """
    BUG-8 FIX: Catch BulkWriteError specifically (partial insert on
    duplicate-key collision) rather than catching all exceptions and
    using a separate DB query to reconstruct which keys were inserted.
    The happy path now only extends `created` with keys that were actually
    inserted successfully.
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
            # All inserted successfully.
            created.extend(candidates)
        except BulkWriteError as bwe:
            # Partial success: some keys had duplicate-key collisions.
            error_indices = {e["index"] for e in bwe.details.get("writeErrors", [])}
            created.extend(c for i, c in enumerate(candidates) if i not in error_indices)
        except Exception:
            # Unexpected error — skip this batch and retry.
            pass
    return created


async def redeem_key(key: str, user_id: int) -> tuple[str, dict | None]:
    """
    Atomically flips an unused key to used, in a single operation.
    Returns (status, doc) where status is one of:
      "ok"        -> doc is the updated key document
      "not_found" -> key never existed (or was revoked)
      "expired"   -> key existed but passed its expiry date
      "used"      -> key was already redeemed by someone else

    BUG-7 FIX: Revoked keys previously fell through to the
    find_one_and_update with status: "unused", which returned None and
    reported "used" — misleading the user. Now revoked keys are mapped
    to "not_found" (treated as invalid from the user's perspective).
    """
    key = key.strip().upper()

    doc = await keys_col.find_one({"key": key})
    if doc is None:
        return "not_found", None

    status = doc.get("status", "")

    # BUG-7 FIX: treat revoked keys as non-existent to the end user.
    if status == "revoked":
        return "not_found", None

    if status == "used":
        return "used", None

    if doc.get("expiry") and doc["expiry"] < now():
        return "expired", None

    # Atomic flip: only succeeds if the key is still "unused" right now.
    updated = await keys_col.find_one_and_update(
        {"key": key, "status": "unused"},
        {"$set": {"status": "used", "used_by": user_id, "used_date": now()}},
        return_document=ReturnDocument.AFTER,
    )
    if updated is None:
        # Another concurrent request won the race.
        return "used", None
    return "ok", updated


async def get_unused_keys(plan: str | None = None, limit: int = 200) -> list[dict]:
    query = {"status": "unused"}
    if plan:
        query["plan"] = plan
    cursor = keys_col.find(query).sort("created_date", -1).limit(limit)
    return [doc async for doc in cursor]


async def get_used_keys(plan: str | None = None, limit: int = 200) -> list[dict]:
    query = {"status": "used"}
    if plan:
        query["plan"] = plan
    cursor = keys_col.find(query).sort("used_date", -1).limit(limit)
    return [doc async for doc in cursor]


async def delete_unused_keys(plan: str | None = None) -> int:
    query = {"status": "unused"}
    if plan:
        query["plan"] = plan
    result = await keys_col.delete_many(query)
    return result.deleted_count


async def revoke_key(key: str) -> bool:
    """Revoke an unused key so it can never be redeemed."""
    result = await keys_col.update_one(
        {"key": key.strip().upper(), "status": "unused"},
        {"$set": {"status": "revoked"}},
    )
    return result.modified_count > 0


async def count_keys(status: str | None = None) -> int:
    query = {} if status is None else {"status": status}
    return await keys_col.count_documents(query)
