from pyrogram import Client, filters
from pyrogram.types import CallbackQuery
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.utils.decorators import admin_only, state_store
from bot.keyboards.admin_kb import admin_back_kb


def welcome_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🖼 Change Welcome Photo", callback_data="admin:welcome:photo")],
        [InlineKeyboardButton("✏️ Change Welcome Message", callback_data="admin:welcome:message")],
        [InlineKeyboardButton("⬅ Back", callback_data="admin:home")],
    ])


@Client.on_callback_query(filters.regex(r"^admin:welcome$"))
@admin_only
async def welcome_menu_handler(client: Client, cb: CallbackQuery):
    await cb.answer()
    await cb.edit_message_text("🖼 **Welcome Settings**", reply_markup=welcome_menu_kb())


@Client.on_callback_query(filters.regex(r"^admin:welcome:photo$"))
@admin_only
async def welcome_photo_prompt(client: Client, cb: CallbackQuery):
    state_store.set(cb.from_user.id, "admin_awaiting:setting_photo:welcome_photo")
    await cb.answer()
    await client.send_message(cb.message.chat.id, "📤 Send the new welcome photo now.", reply_markup=admin_back_kb("admin:welcome"))


@Client.on_callback_query(filters.regex(r"^admin:welcome:message$"))
@admin_only
async def welcome_message_prompt(client: Client, cb: CallbackQuery):
    state_store.set(cb.from_user.id, "admin_awaiting:setting_text:welcome_message")
    await cb.answer()
    await client.send_message(cb.message.chat.id, "✏️ Send the new welcome message text now.", reply_markup=admin_back_kb("admin:welcome"))
