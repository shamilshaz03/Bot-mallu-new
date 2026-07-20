from pyrogram import Client, filters
from pyrogram.types import Message

from bot.utils.decorators import state_store
from bot.database.keys import redeem_key
from bot.database.users import apply_activation, get_user
from bot.database.plans import get_plan
from bot.strings import KEY_INVALID, KEY_ALREADY_USED, KEY_ACTIVATED
from bot.keyboards.user_kb import start_menu_kb
from bot.utils.logger import logger


def _is_awaiting_key(_, __, message: Message) -> bool:
    state = state_store.get(message.from_user.id) if message.from_user else None
    return bool(state and state["step"] == "awaiting_activation_key")


awaiting_key_filter = filters.create(_is_awaiting_key)


@Client.on_message(filters.private & filters.text & awaiting_key_filter)
async def activation_key_handler(client: Client, message: Message):
    user_id = message.from_user.id
    state = state_store.get(user_id)
    state_store.clear(user_id)  # consume the state regardless of outcome

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

    logger.info("User %s activated plan %s using key %s", user_id, plan_id, redeemed["key"])

    await message.reply_text(
        KEY_ACTIVATED.format(plan=plan_title),
        reply_markup=start_menu_kb(),
    )
