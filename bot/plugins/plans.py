from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from bot.database.users import get_user, owned_plans
from bot.database.plans import get_plan
from bot.database.samples import get_samples
from bot.database.settings import get_setting
from bot.keyboards.user_kb import plans_list_kb, plan_view_kb, get_more_kb
from bot.strings import ENTER_KEY_PROMPT


@Client.on_callback_query(filters.regex(r"^plans:list$"))
async def plans_list_handler(client: Client, cb: CallbackQuery):
    user = await get_user(cb.from_user.id)
    await cb.answer()
    try:
        await cb.edit_message_text("💎 **Choose a Plan**", reply_markup=plans_list_kb(user))
    except Exception:
        await client.send_message(cb.message.chat.id, "💎 **Choose a Plan**", reply_markup=plans_list_kb(user))


@Client.on_callback_query(filters.regex(r"^plan:view:(\d+)$"))
async def plan_view_handler(client: Client, cb: CallbackQuery):
    plan_id = cb.matches[0].group(1)
    plan = await get_plan(plan_id)
    if not plan:
        await cb.answer("Plan not found.", show_alert=True)
        return

    await cb.answer()

    user = await get_user(cb.from_user.id)
    owned = plan_id in owned_plans(user)

    text = (
        f"💎 **{plan['title']}** — ₹{plan['price']}\n\n"
        f"{plan['description']}\n\n"
        "👇 Preview samples below:"
    )
    try:
        await cb.edit_message_text(text, reply_markup=plan_view_kb(plan_id, owned))
    except Exception:
        await client.send_message(cb.message.chat.id, text, reply_markup=plan_view_kb(plan_id, owned))

    samples = await get_samples(plan_id)
    if not samples:
        await client.send_message(cb.message.chat.id, "No samples uploaded for this plan yet.")
        return

    for sample in samples:
        caption = sample.get("caption", "")
        file_type = sample["file_type"]
        file_id = sample["file_id"]
        if file_type == "photo":
            await client.send_photo(cb.message.chat.id, file_id, caption=caption)
        elif file_type == "video":
            await client.send_video(cb.message.chat.id, file_id, caption=caption)
        else:
            await client.send_document(cb.message.chat.id, file_id, caption=caption)


@Client.on_callback_query(filters.regex(r"^plan:getmore:(\d+)$"))
async def plan_getmore_handler(client: Client, cb: CallbackQuery):
    plan_id = cb.matches[0].group(1)
    await cb.answer()

    qr = await get_setting("payment_qr")
    payment_details = await get_setting("payment_details") or "Payment details not configured yet."

    caption = f"💰 **Payment Details**\n\n{payment_details}\n\nAfter payment, contact admin or enter your activation key."

    if qr:
        await client.send_photo(cb.message.chat.id, qr, caption=caption, reply_markup=get_more_kb(plan_id))
    else:
        await client.send_message(cb.message.chat.id, caption, reply_markup=get_more_kb(plan_id))


@Client.on_callback_query(filters.regex(r"^activate:start:(\d+)$"))
async def activate_start_handler(client: Client, cb: CallbackQuery):
    from bot.utils.decorators import state_store

    plan_id = cb.matches[0].group(1)
    state_store.set(cb.from_user.id, "awaiting_activation_key", {"plan": plan_id})
    await cb.answer()
    await client.send_message(cb.message.chat.id, ENTER_KEY_PROMPT)
