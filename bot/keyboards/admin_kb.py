"""
Admin-facing keyboards.

REQ-38 FIX: Added "📋 Content Library" to admin_panel_kb so admins can
browse, edit captions, and delete content entirely from the button UI —
no slash commands required for daily management.
"""
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.config import config


def admin_panel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🖼 Welcome Settings",  callback_data="admin:welcome")],
        [InlineKeyboardButton("💳 Manage Plans",      callback_data="admin:plans")],
        [InlineKeyboardButton("🎁 Manage Samples",    callback_data="admin:samples")],
        [InlineKeyboardButton("📤 Upload Content",    callback_data="admin:upload")],
        # REQ-38 FIX: button-based edit/delete of existing content.
        [InlineKeyboardButton("📋 Content Library",   callback_data="admin:contentlib")],
        [InlineKeyboardButton("🔑 Activation Keys",   callback_data="admin:keys")],
        [InlineKeyboardButton("📢 Broadcast",         callback_data="admin:broadcast")],
        [InlineKeyboardButton("📊 Statistics",        callback_data="admin:stats")],
        [InlineKeyboardButton("💰 Payment Settings",  callback_data="admin:payment")],
        [InlineKeyboardButton("❌ Close",             callback_data="admin:close")],
    ])


def admin_back_kb(target: str = "admin:home") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data=target)]])


def admin_plan_select_kb(prefix: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(f"₹{p} Plan", callback_data=f"{prefix}:{p}")] for p in config.PLAN_IDS]
    rows.append([InlineKeyboardButton("⬅️ Back", callback_data="admin:home")])
    return InlineKeyboardMarkup(rows)


def admin_plan_edit_kb(plan_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Edit Title",       callback_data=f"admin:planfield:{plan_id}:title")],
        [InlineKeyboardButton("✏️ Edit Description", callback_data=f"admin:planfield:{plan_id}:description")],
        [InlineKeyboardButton("✏️ Edit Price",       callback_data=f"admin:planfield:{plan_id}:price")],
        [InlineKeyboardButton("⬅️ Back",             callback_data="admin:plans")],
    ])


def admin_keys_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Generate Keys",        callback_data="admin:keys:gen")],
        [InlineKeyboardButton("📄 View Unused Keys",     callback_data="admin:keys:unused")],
        [InlineKeyboardButton("📄 View Used Keys",       callback_data="admin:keys:used")],
        [InlineKeyboardButton("🗑 Delete Unused Keys",   callback_data="admin:keys:delunused")],
        [InlineKeyboardButton("⬅️ Back",                callback_data="admin:home")],
    ])


def admin_key_count_kb(plan_id: str) -> InlineKeyboardMarkup:
    counts = [1, 5, 10, 50]
    row = [InlineKeyboardButton(str(c), callback_data=f"admin:keys:doGen:{plan_id}:{c}") for c in counts]
    return InlineKeyboardMarkup([row, [InlineKeyboardButton("⬅️ Back", callback_data="admin:keys")]])


def admin_upload_category_kb(plan_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎥 Videos", callback_data=f"admin:upload:cat:{plan_id}:videos"),
            InlineKeyboardButton("📷 Photos", callback_data=f"admin:upload:cat:{plan_id}:photos"),
            InlineKeyboardButton("📁 Files",  callback_data=f"admin:upload:cat:{plan_id}:files"),
        ],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin:home")],
    ])


# ── Content Library keyboards ──────────────────────────────────────────────

def admin_contentlib_plan_kb() -> InlineKeyboardMarkup:
    """Plan selection for the content library (browse/edit/delete existing content)."""
    rows = [
        [InlineKeyboardButton(f"₹{p} Plan", callback_data=f"admin:clplan:{p}")]
        for p in config.PLAN_IDS
    ]
    rows.append([InlineKeyboardButton("⬅️ Back", callback_data="admin:home")])
    return InlineKeyboardMarkup(rows)


def admin_content_item_kb(oid: str, plan_id: str, page: int) -> InlineKeyboardMarkup:
    """Inline buttons attached to each content item in the library."""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✏️ Edit Caption", callback_data=f"admin:clitem:edit:{oid}:{plan_id}:{page}"),
        InlineKeyboardButton("🗑 Delete",        callback_data=f"admin:clitem:del:{oid}:{plan_id}:{page}"),
    ]])


def admin_content_del_confirm_kb(oid: str, plan_id: str, page: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Yes, Delete", callback_data=f"admin:clitem:del:yes:{oid}:{plan_id}:{page}"),
        InlineKeyboardButton("❌ Cancel",      callback_data=f"admin:contentlib:{plan_id}:{page}"),
    ]])


def admin_contentlib_nav_kb(plan_id: str, page: int, total_pages: int) -> InlineKeyboardMarkup:
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"admin:contentlib:{plan_id}:{page - 1}"))
    nav.append(InlineKeyboardButton(f"{page} / {total_pages}", callback_data="noop"))
    if page < total_pages:
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"admin:contentlib:{plan_id}:{page + 1}"))
    rows = [nav] if nav else []
    rows.append([InlineKeyboardButton("🏠 Admin Home", callback_data="admin:home")])
    return InlineKeyboardMarkup(rows)


def confirm_kb(yes_cb: str, no_cb: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Confirm", callback_data=yes_cb),
        InlineKeyboardButton("❌ Cancel",  callback_data=no_cb),
    ]])
