from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.database.users import ensure_user
from bot.database.settings import get_setting
from bot.keyboards.user_kb import start_menu_kb
from bot.strings import MAINTENANCE_MSG
from bot.config import config
from bot.utils.logger import logger
from bot.utils.log_channel import send_log


async def _check_force_join(client: Client, user_id: int) -> bool:
    """
    BUG-10 FIX: Enforce FORCE_JOIN_CHANNEL if configured.
    Returns True if the user is a member (or no channel is configured).
    """
    if not config.FORCE_JOIN_CHANNEL:
        return True
    try:
        from pyrogram.enums import ChatMemberStatus
        member = await client.get_chat_member(config.FORCE_JOIN_CHANNEL, user_id)
        return member.status not in (ChatMemberStatus.BANNED, ChatMemberStatus.LEFT)
    except Exception:
        # If we can't check (bot not in channel, etc.), allow through to
        # avoid locking out everyone due to a config mistake.
        return True


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

    # BUG-10 FIX: Enforce channel membership before granting access.
    if not await _check_force_join(client, message.from_user.id):
        channel = config.FORCE_JOIN_CHANNEL.lstrip("@")
        await message.reply_text(
            "👋 Please join our channel first to use this bot!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{channel}"),
                InlineKeyboardButton("✅ I Joined", callback_data="check:join"),
            ]]),
        )
        return

    logger.info("User %s started the bot", message.from_user.id)
    # BUG-11: log new/returning user activity to LOG_CHANNEL
    await send_log(client, f"👤 /start — user `{message.from_user.id}` (@{message.from_user.username})")
    await send_welcome(
        client, message.chat.id, message.from_user.id,
        message.from_user.username, message.from_user.first_name,
    )


@Client.on_callback_query(filters.regex(r"^check:join$"))
async def check_join_handler(client: Client, cb: CallbackQuery):
    """Re-check membership after user taps 'I Joined'."""
    if await _check_force_join(client, cb.from_user.id):
        await cb.answer("✅ Access granted!", show_alert=False)
        await cb.message.delete()
        await send_welcome(
            client, cb.message.chat.id, cb.from_user.id,
            cb.from_user.username, cb.from_user.first_name,
        )
    else:
        await cb.answer("❌ You haven't joined yet. Please join and try again.", show_alert=True)


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
