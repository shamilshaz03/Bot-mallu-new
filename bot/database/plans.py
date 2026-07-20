from bot.database.connection import plans_col


async def get_plan(plan_id: str) -> dict | None:
    return await plans_col.find_one({"plan_id": plan_id})


async def get_all_plans() -> list[dict]:
    cursor = plans_col.find({}).sort("price", 1)
    return [doc async for doc in cursor]


async def update_plan_field(plan_id: str, field: str, value) -> None:
    assert field in {"title", "description", "price"}, "Only these fields are admin-editable"
    await plans_col.update_one({"plan_id": plan_id}, {"$set": {field: value}})
