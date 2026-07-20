from bot.database.users import count_users, count_active_subscribers, count_plan_subscribers
from bot.database.keys import count_keys
from bot.database.contents import count_content
from bot.config import config


async def build_statistics_report() -> str:
    total_users = await count_users()
    active_subs = await count_active_subscribers()

    plan_lines = []
    for plan_id in config.PLAN_IDS:
        subs = await count_plan_subscribers(plan_id)
        content_count = await count_content(plan_id)
        plan_lines.append(f"₹{plan_id} Plan → {subs} subscribers, {content_count} items")

    unused_keys = await count_keys("unused")
    used_keys = await count_keys("used")

    report = (
        "📊 **Bot Statistics**\n\n"
        f"👥 Total Users: {total_users}\n"
        f"✅ Active Subscribers: {active_subs}\n\n"
        "**Plan-wise Subscribers:**\n" + "\n".join(plan_lines) + "\n\n"
        f"🔑 Unused Keys: {unused_keys}\n"
        f"🔓 Used Keys: {used_keys}"
    )
    return report
