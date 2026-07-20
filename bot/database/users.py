from bot.database.connection import users_col
from bot.database.models import new_user_doc, now
from bot.config import config


async def get_user(user_id: int) -> dict | None:
    return await users_col.find_one({"user_id": user_id})


async def ensure_user(user_id: int, username: str | None, first_name: str | None) -> dict:
    user = await get_user(user_id)
    if user is None:
        doc = new_user_doc(user_id, username, first_name)
        await users_col.insert_one(doc)
        return doc
    await users_col.update_one(
        {"user_id": user_id},
        {"$set": {"last_active_date": now(), "username": username, "first_name": first_name}},
    )
    user["last_active_date"] = now()
    return user


async def apply_activation(user_id: int, plan: str) -> None:
    """
    Update subscription after a key is redeemed.

    BUG-5 FIX: Changed >= to > so re-activating the same plan does NOT
    push it into previous_plans (which caused duplicate entries to accumulate).
    Also enforces deduplication in previous_plans on every write.
    """
    user = await get_user(user_id)
    previous_plans: list[str] = list(user.get("previous_plans", [])) if user else []
    current_plan: str | None = user.get("current_plan") if user else None

    if current_plan is None or config.PLAN_RANK.get(plan, 0) > config.PLAN_RANK.get(current_plan, 0):
        # Genuine upgrade — archive current.
        if current_plan and current_plan not in previous_plans:
            previous_plans.append(current_plan)
        new_current = plan
    elif plan == current_plan:
        # Re-activation of same plan — just refresh date.
        new_current = current_plan
    else:
        # Lower-ranked plan — keep current, record new plan as owned.
        new_current = current_plan
        if plan not in previous_plans:
            previous_plans.append(plan)

    # Deduplicate in case of any historical data issues.
    previous_plans = list(dict.fromkeys(previous_plans))

    await users_col.update_one(
        {"user_id": user_id},
        {"$set": {
            "current_plan": new_current,
            "previous_plans": previous_plans,
            "activation_date": now(),
            "subscription_status": "active",
        }},
        upsert=True,
    )


def owned_plans(user: dict | None) -> set[str]:
    """All plan IDs the user has ever activated (current + all previous)."""
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
