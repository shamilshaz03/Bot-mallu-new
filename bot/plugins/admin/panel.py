from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery

from bot.utils.decorators import admin_only, state_store
from bot.keyboards.admin_kb import admin_panel_kb


@Client.on_message(filters.command("admin") & filters.private)
@admin_only
async def admin_command(client: Client, message: Message):
    state_store.clear(message.from_user.id)
    await message.reply_text("🛠 **Admin Panel**\n\nChoose a section below:", reply_markup=admin_panel_kb())


@Client.on_callback_query(filters.regex(r"^admin:home$"))
@admin_only
async def admin_home_handler(client: Client, cb: CallbackQuery):
    state_store.clear(cb.from_user.id)
    await cb.answer()
    try:
        await cb.edit_message_text("🛠 **Admin Panel**\n\nChoose a section below:", reply_markup=admin_panel_kb())
    except Exception:
        await client.send_message(cb.message.chat.id, "🛠 **Admin Panel**", reply_markup=admin_panel_kb())


@Client.on_callback_query(filters.regex(r"^admin:close$"))
@admin_only
async def admin_close_handler(client: Client, cb: CallbackQuery):
    state_store.clear(cb.from_user.id)
    await cb.answer()
    try:
        await cb.message.delete()
    except Exception:
        pass


# BUG-9 FIX: /cancel command lets admins abort any multi-step flow
# (upload content, broadcast, plan edit, etc.) without getting permanently
# stuck in a state until the bot restarts.
@Client.on_message(filters.command("cancel") & filters.private)
@admin_only
async def cancel_handler(client: Client, message: Message):
    state = state_store.get(message.from_user.id)
    state_store.clear(message.from_user.id)
    if state:
        await message.reply_text(
            f"✅ Action cancelled (was: `{state['step']}`).\n\nUse /admin to open the panel.",
        )
    else:
        await message.reply_text("Nothing to cancel. Use /admin to open the panel.")
