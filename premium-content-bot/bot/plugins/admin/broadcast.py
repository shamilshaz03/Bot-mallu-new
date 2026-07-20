"""
Broadcast a message to all registered users.

BUG-13 FIX: FloodWait retry + 50 ms inter-user delay.
BUG-11: Log broadcast result to LOG_CHANNEL.
"""
import asyncio

from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import CallbackQuery, Message

from bot.utils.decorators import admin_only, state_store
from bot.database.users import all_user_ids
from bot.config import config
from bot.utils.logger import logger
from bot.utils.log_channel import send_log


@Client.on_callback_query(filters.regex(r"^admin:broadcast$"))
@admin_only
async def broadcast_prompt(client: Client, cb: CallbackQuery):
    state_store.set(cb.from_user.id, "admin_awaiting:broadcast")
    await cb.answer()
    await client.send_message(
        cb.message.chat.id,
        "📢 **Broadcast**\n\n"
        "Send the message or media you want to broadcast to all users now.\n\n"
        "Send /cancel to abort.",
    )


def _awaiting_broadcast(_, __, message: Message) -> bool:
    if not message.from_user or message.from_user.id not in config.ADMIN_IDS:
        return False
    state = state_store.get(message.from_user.id)
    return bool(state and state["step"] == "admin_awaiting:broadcast")


awaiting_broadcast_filter = filters.create(_awaiting_broadcast)


@Client.on_message(filters.private & awaiting_broadcast_filter)
@admin_only
async def broadcast_execute(client: Client, message: Message):
    state_store.clear(message.from_user.id)

    user_ids   = await all_user_ids()
    status_msg = await message.reply_text(f"📢 Broadcasting to {len(user_ids)} users…")

    sent, failed = 0, 0
    for uid in user_ids:
        try:
            await message.copy(uid)
            sent += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            try:
                await message.copy(uid)
                sent += 1
            except Exception:
                failed += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)

    logger.info("Broadcast done: %d sent, %d failed", sent, failed)
    result = f"✅ **Broadcast complete**\n\nSent: {sent}\nFailed: {failed}"
    await status_msg.edit_text(result)

    await send_log(
        client,
        f"📢 Broadcast by admin `{message.from_user.id}` — sent: **{sent}**, failed: **{failed}**",
    )
