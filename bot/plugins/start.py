from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery

from bot.database.users import ensure_user
from bot.database.settings import get_setting
from bot.keyboards.user_kb import start_menu_kb
from bot.strings import MAINTENANCE_MSG
from bot.config import config
from bot.utils.logger import logger


async def send_welcome(client: Client, chat_id: int, user_id: int, username, first_name):
    await ensure_user(user_id, username, first_name)

    welcome_photo = await get_setting("welcome_photo")
    welcome_message = await get_setting("welcome_message") or "👋 Welcome!"

    if welcome_photo:
        await client.send_photo(chat_id, welcome_photo, caption=welcome_message, reply_markup=start_menu_kb())
    else:
        await client.send_message(chat_id, welcome_message, reply_markup=start_menu_kb())


@Client.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    maintenance = await get_setting("maintenance_mode")
    if maintenance and message.from_user.id not in config.ADMIN_IDS:
        await message.reply_text(MAINTENANCE_MSG)
        return

    logger.info("User %s started the bot", message.from_user.id)
    await send_welcome(
        client, message.chat.id, message.from_user.id,
        message.from_user.username, message.from_user.first_name,
    )


@Client.on_callback_query(filters.regex(r"^start:back$"))
async def start_back_handler(client: Client, cb: CallbackQuery):
    welcome_photo = await get_setting("welcome_photo")
    welcome_message = await get_setting("welcome_message") or "👋 Welcome!"

    try:
        if welcome_photo:
            await cb.message.delete()
            await client.send_photo(cb.message.chat.id, welcome_photo, caption=welcome_message, reply_markup=start_menu_kb())
        else:
            await cb.edit_message_text(welcome_message, reply_markup=start_menu_kb())
    except Exception:
        await client.send_message(cb.message.chat.id, welcome_message, reply_markup=start_menu_kb())
    await cb.answer()


@Client.on_callback_query(filters.regex(r"^contact:admin$"))
async def contact_admin_handler(client: Client, cb: CallbackQuery):
    contact = await get_setting("contact_admin") or "Contact info not set."
    await cb.answer()
    await client.send_message(cb.message.chat.id, f"📞 Contact Admin: {contact}")


@Client.on_callback_query(filters.regex(r"^noop$"))
async def noop_handler(client: Client, cb: CallbackQuery):
    await cb.answer()
