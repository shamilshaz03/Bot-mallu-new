from bot.database.connection import users_col
from bot.database.models import new_user_doc, now
from bot.config import config


async def get_user(user_id: int) -> dict | None:
    return await users_col.find_one({"user_id": user_id})


async def ensure_user(user_id: int, username: str | None, first_name: str | None) -> dict:
    """Get the user, creating them if they don't exist yet. Always refreshes last_active_date."""
    user = await get_user(user_id)
    if user is None:
        doc = new_user_doc(user_id, username, first_name)
        await users_col.insert_one(doc)
        return doc

    await users_col.update_one(
        {"user_id": user_id},
        {"$set": {
            "last_active_date": now(),
            "username": username,
            "first_name": first_name,
        }},
    )
    user["last_active_date"] = now()
    return user


async def apply_activation(user_id: int, plan: str) -> None:
    """Update a user's subscription after a key is successfully redeemed.
    Preserves previous plans (upgrade logic) and never removes access already granted.
    """
    user = await get_user(user_id)
    previous_plans = list(user.get("previous_plans", [])) if user else []
    current_plan = user.get("current_plan") if user else None

    if current_plan and current_plan not in previous_plans:
        previous_plans.append(current_plan)

    # Only "upgrade" if the new plan ranks higher than the current one
    if current_plan is None or config.PLAN_RANK.get(plan, 0) >= config.PLAN_RANK.get(current_plan, 0):
        new_current = plan
    else:
        new_current = current_plan
        if plan not in previous_plans:
            previous_plans.append(plan)

    await users_col.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "current_plan": new_current,
                "previous_plans": previous_plans,
                "activation_date": now(),
                "subscription_status": "active",
            }
        },
        upsert=True,
    )


def owned_plans(user: dict | None) -> set[str]:
    """All plan ids the user currently has access to (current + previous, since access is never revoked)."""
    if not user:
        return set()
    owned = set(user.get("previous_plans", []))
    if user.get("current_plan"):
        owned.add(user["current_plan"])
    return owned


async def count_users() -> int:
    return await users_col.count_documents({})


async def count_active_subscribers() -> int:
    return await users_col.count_documents({"subscription_status": "active"})


async def count_plan_subscribers(plan: str) -> int:
    return await users_col.count_documents({"current_plan": plan})


async def all_user_ids() -> list[int]:
    cursor = users_col.find({}, {"user_id": 1})
    return [doc["user_id"] async for doc in cursor]
