"""
Generic capture handlers for simple "admin sends one text/photo -> saved to
a settings key" flows (welcome message/photo, payment details/QR, contact
admin). Reduces duplication across welcome.py and payment_settings.py.
"""
from pyrogram import Client, filters
from pyrogram.types import Message

from bot.utils.decorators import admin_only, state_store
from bot.database.settings import set_setting
from bot.config import config


def _awaiting_setting_text(_, __, message: Message) -> bool:
    if not message.from_user or message.from_user.id not in config.ADMIN_IDS:
        return False
    state = state_store.get(message.from_user.id)
    return bool(state and state["step"].startswith("admin_awaiting:setting_text:"))


def _awaiting_setting_photo(_, __, message: Message) -> bool:
    if not message.from_user or message.from_user.id not in config.ADMIN_IDS:
        return False
    state = state_store.get(message.from_user.id)
    return bool(state and state["step"].startswith("admin_awaiting:setting_photo:"))


awaiting_setting_text_filter = filters.create(_awaiting_setting_text)
awaiting_setting_photo_filter = filters.create(_awaiting_setting_photo)


@Client.on_message(filters.private & filters.text & awaiting_setting_text_filter)
@admin_only
async def capture_setting_text(client: Client, message: Message):
    state = state_store.get(message.from_user.id)
    setting_key = state["step"].split(":", 2)[2]
    state_store.clear(message.from_user.id)

    await set_setting(setting_key, message.text.strip())
    await message.reply_text(f"✅ `{setting_key}` updated successfully.")


@Client.on_message(filters.private & filters.photo & awaiting_setting_photo_filter)
@admin_only
async def capture_setting_photo(client: Client, message: Message):
    state = state_store.get(message.from_user.id)
    setting_key = state["step"].split(":", 2)[2]
    state_store.clear(message.from_user.id)

    file_id = message.photo.file_id
    await set_setting(setting_key, file_id)
    await message.reply_text(f"✅ `{setting_key}` updated successfully.")
