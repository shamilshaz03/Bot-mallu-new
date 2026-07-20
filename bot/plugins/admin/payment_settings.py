from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.utils.decorators import admin_only, state_store


def payment_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🖼 Change QR Code", callback_data="admin:payment:qr")],
        [InlineKeyboardButton("✏️ Change Payment Details", callback_data="admin:payment:details")],
        [InlineKeyboardButton("📞 Change Contact Admin", callback_data="admin:payment:contact")],
        [InlineKeyboardButton("⬅ Back", callback_data="admin:home")],
    ])


@Client.on_callback_query(filters.regex(r"^admin:payment$"))
@admin_only
async def payment_menu_handler(client: Client, cb: CallbackQuery):
    await cb.answer()
    await cb.edit_message_text("💰 **Payment Settings**", reply_markup=payment_menu_kb())


@Client.on_callback_query(filters.regex(r"^admin:payment:qr$"))
@admin_only
async def payment_qr_prompt(client: Client, cb: CallbackQuery):
    state_store.set(cb.from_user.id, "admin_awaiting:setting_photo:payment_qr")
    await cb.answer()
    await client.send_message(cb.message.chat.id, "📤 Send the new payment QR code image now.")


@Client.on_callback_query(filters.regex(r"^admin:payment:details$"))
@admin_only
async def payment_details_prompt(client: Client, cb: CallbackQuery):
    state_store.set(cb.from_user.id, "admin_awaiting:setting_text:payment_details")
    await cb.answer()
    await client.send_message(cb.message.chat.id, "✏️ Send the new payment details text (bank/UPI info) now.")


@Client.on_callback_query(filters.regex(r"^admin:payment:contact$"))
@admin_only
async def contact_admin_prompt(client: Client, cb: CallbackQuery):
    state_store.set(cb.from_user.id, "admin_awaiting:setting_text:contact_admin")
    await cb.answer()
    await client.send_message(cb.message.chat.id, "✏️ Send the new contact admin text (e.g. @username) now.")
