"""
User-facing keyboards.

REQ-23 FIX: plans_list_kb now shows the correct status labels:
  👑 Current Plan  — the user's active plan
  ✅ Subscribed    — a plan the user previously owned (still has access)
  ⬆️ Upgrade       — a higher-tier plan the user doesn't own yet
  (no prefix)      — plan not yet purchased
"""
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.config import config
from bot.database.users import owned_plans


def start_menu_kb() -> InlineKeyboardMarkup:
    # REQ-4: Start Menu contains ONLY these two buttons.
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Plans", callback_data="plans:list")],
        [InlineKeyboardButton("📞 Contact Admin", callback_data="contact:admin")],
    ])


def plans_list_kb(user: dict | None, plans: list[dict] | None = None) -> InlineKeyboardMarkup:
    """
    REQ-23: Correctly labels each plan according to the user's subscription.

    plans — optional list of plan dicts fetched from MongoDB so we can show
            the real title and price instead of the bare plan_id number.
    """
    owned = owned_plans(user)
    current = user.get("current_plan") if user else None
    plan_map = {p["plan_id"]: p for p in (plans or [])}

    rows = []
    for plan_id in config.PLAN_IDS:
        pdata = plan_map.get(plan_id, {})
        title = pdata.get("title", f"₹{plan_id} Plan")
        price = pdata.get("price", plan_id)

        if plan_id == current:
            label = f"👑  ₹{price} — {title}"
            label += "  •  Current Plan"
        elif plan_id in owned:
            # Previously owned (e.g. ₹199 after upgrading to ₹299).
            label = f"✅  ₹{price} — {title}"
            label += "  •  Subscribed"
        elif current and config.PLAN_RANK.get(plan_id, 0) > config.PLAN_RANK.get(current, 0):
            # Higher tier than the user's current plan.
            label = f"⬆️  ₹{price} — {title}"
            label += "  •  Upgrade"
        else:
            label = f"💎  ₹{price} — {title}"

        rows.append([InlineKeyboardButton(label, callback_data=f"plan:view:{plan_id}")])

    rows.append([InlineKeyboardButton("⬅️ Back", callback_data="start:back")])
    return InlineKeyboardMarkup(rows)


def plan_view_kb(plan_id: str, has_access: bool = False) -> InlineKeyboardMarkup:
    rows = []
    if has_access:
        rows.append([InlineKeyboardButton("📂 Browse Content", callback_data=f"feed:start:{plan_id}")])
    rows.append([InlineKeyboardButton("🔓 Get More", callback_data=f"plan:getmore:{plan_id}")])
    rows.append([InlineKeyboardButton("⬅️ Back to Plans", callback_data="plans:list")])
    return InlineKeyboardMarkup(rows)


def get_more_kb(plan_id: str) -> InlineKeyboardMarkup:
    # REQ-11: Contact Admin + Enter Activation Key buttons.
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📞 Contact Admin", callback_data="contact:admin")],
        [InlineKeyboardButton("🔑 Enter Activation Key", callback_data=f"activate:start:{plan_id}")],
        [InlineKeyboardButton("⬅️ Back", callback_data=f"plan:view:{plan_id}")],
    ])


def content_nav_kb(plan_id: str, page: int, total_pages: int, category: str | None = None) -> InlineKeyboardMarkup:
    # BUG-15 FIX: guard against total_pages < 1 so the nav row is never empty.
    safe_total = max(total_pages, 1)
    cat = category or "-"

    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"feed:page:{plan_id}:{page - 1}:{cat}"))
    if page < safe_total:
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"feed:page:{plan_id}:{page + 1}:{cat}"))

    rows: list[list] = []
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(f"📄 Page {page} / {safe_total}", callback_data="noop")])

    # REQ-29/30: category browsing exclusive to ₹799.
    if plan_id == "799":
        rows.append([
            InlineKeyboardButton("🎥 Videos", callback_data="feed:cat:799:videos"),
            InlineKeyboardButton("📷 Photos", callback_data="feed:cat:799:photos"),
            InlineKeyboardButton("📁 Files", callback_data="feed:cat:799:files"),
        ])

    rows.append([InlineKeyboardButton("⬅️ Back to Plans", callback_data="plans:list")])
    return InlineKeyboardMarkup(rows)


def after_activation_kb(plan_id: str) -> InlineKeyboardMarkup:
    """REQ-25: Shown immediately after successful key activation."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📂 View My Content Now", callback_data=f"feed:start:{plan_id}")],
        [InlineKeyboardButton("💎 All Plans", callback_data="plans:list")],
    ])


def back_to_start_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="start:back")]])
