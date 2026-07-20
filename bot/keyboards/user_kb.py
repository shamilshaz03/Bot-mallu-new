from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.config import config
from bot.database.users import owned_plans


def start_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Plans", callback_data="plans:list")],
        [InlineKeyboardButton("📞 Contact Admin", callback_data="contact:admin")],
    ])


def plans_list_kb(user: dict | None) -> InlineKeyboardMarkup:
    owned = owned_plans(user)
    current = user.get("current_plan") if user else None

    rows = []
    for plan_id in config.PLAN_IDS:
        if plan_id == current:
            label = f"👑 ₹{plan_id} Plan (Current)"
        elif plan_id in owned:
            label = f"✅ ₹{plan_id} Plan (Owned)"
        else:
            label = f"₹{plan_id} Plan"
        rows.append([InlineKeyboardButton(label, callback_data=f"plan:view:{plan_id}")])

    rows.append([InlineKeyboardButton("⬅ Back", callback_data="start:back")])
    return InlineKeyboardMarkup(rows)


def plan_view_kb(plan_id: str, owned: bool = False) -> InlineKeyboardMarkup:
    rows = []
    if owned:
        rows.append([InlineKeyboardButton("📂 View Content", callback_data=f"feed:start:{plan_id}")])
    rows.append([InlineKeyboardButton("🔓 Get More", callback_data=f"plan:getmore:{plan_id}")])
    rows.append([InlineKeyboardButton("⬅ Back to Plans", callback_data="plans:list")])
    return InlineKeyboardMarkup(rows)


def get_more_kb(plan_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📞 Contact Admin", callback_data="contact:admin")],
        [InlineKeyboardButton("🔑 Enter Activation Key", callback_data=f"activate:start:{plan_id}")],
        [InlineKeyboardButton("⬅ Back", callback_data=f"plan:view:{plan_id}")],
    ])


def content_nav_kb(plan_id: str, page: int, total_pages: int, category: str | None = None) -> InlineKeyboardMarkup:
    nav_row = []
    cat = category or "-"
    if page > 1:
        nav_row.append(InlineKeyboardButton("⬅ Previous", callback_data=f"feed:page:{plan_id}:{page-1}:{cat}"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton("➡ Next", callback_data=f"feed:page:{plan_id}:{page+1}:{cat}"))


    rows = [nav_row] if nav_row else []
    rows.append([InlineKeyboardButton(f"Page {page}/{max(total_pages,1)}", callback_data="noop")])

    if plan_id == "799":
        rows.append([
            InlineKeyboardButton("🎥 Videos", callback_data="feed:cat:799:videos"),
            InlineKeyboardButton("📷 Photos", callback_data="feed:cat:799:photos"),
            InlineKeyboardButton("📁 Files", callback_data="feed:cat:799:files"),
        ])

    rows.append([InlineKeyboardButton("⬅ Back to Plans", callback_data="plans:list")])
    return InlineKeyboardMarkup(rows)


def back_to_start_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅ Back", callback_data="start:back")]])
