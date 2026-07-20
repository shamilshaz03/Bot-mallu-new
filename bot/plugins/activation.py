"""
Handles the activation key redemption flow for regular users.

REQ-13/17/19: Keys are single-use, unique, and atomically validated.
REQ-25 FIX: After successful activation the bot immediately shows a
            "View My Content Now" button — content is one tap away.
"""
from pyrogram import Client, filters
from pyrogram.types import Message

from bot.utils.decorators import state_store
from bot.database.keys import redeem_key
from bot.database.users import apply_activation
from bot.database.plans import get_plan
from bot.strings import KEY_INVALID, KEY_ALREADY_USED, KEY_ACTIVATED
from bot.keyboards.user_kb import after_activation_kb
from bot.utils.logger import logger
from bot.utils.log_channel import send_log


def _is_awaiting_key(_, __, message: Message) -> bool:
    if not message.from_user:
        return False
    state = state_store.get(message.from_user.id)
    return bool(state and state["step"] == "awaiting_activation_key")


awaiting_key_filter = filters.create(_is_awaiting_key)


@Client.on_message(filters.private & filters.text & awaiting_key_filter)
async def activation_key_handler(client: Client, message: Message):
    user_id = message.from_user.id
    state_store.clear(user_id)  # consume state regardless of outcome

    key_text = message.text.strip()

    status, redeemed = await redeem_key(key_text, user_id)

    if status == "used":
        await message.reply_text(KEY_ALREADY_USED)
        return
    if status in ("not_found", "expired"):
        await message.reply_text(KEY_INVALID)
        return

    plan_id = redeemed["plan"]
    await apply_activation(user_id, plan_id)

    plan = await get_plan(plan_id)
    plan_title = plan["title"] if plan else f"₹{plan_id} Plan"

    logger.info("User %s activated plan %s with key %s", user_id, plan_id, redeemed["key"])

    # BUG-11: log key redemption to admin channel.
    await send_log(
        client,
        f"🔑 Key redeemed — user `{user_id}` activated **{plan_title}** "
        f"with key `{redeemed['key']}`",
    )

    # REQ-25 FIX: Show "View My Content Now" button immediately after activation.
    await message.reply_text(
        KEY_ACTIVATED.format(plan=plan_title),
        reply_markup=after_activation_kb(plan_id),
    )
