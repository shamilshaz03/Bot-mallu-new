"""
User-facing plan browsing and sample previews.

REQ-7/8/9: Samples are admin-curated and never reveal premium content.
REQ-10/11: Every plan page has a Get More button.
BUG-13 FIX: FloodWait retry + 0.35 s inter-message delay when sending samples.
"""
import asyncio

from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import CallbackQuery

from bot.database.users import get_user, owned_plans
from bot.database.plans import get_plan, get_all_plans
from bot.database.samples import get_samples
from bot.database.settings import get_setting
from bot.keyboards.user_kb import plans_list_kb, plan_view_kb, get_more_kb
from bot.strings import ENTER_KEY_PROMPT
from bot.utils.logger import logger


@Client.on_callback_query(filters.regex(r"^plans:list$"))
async def plans_list_handler(client: Client, cb: CallbackQuery):
    # Fetch user and all plans in parallel for performance.
    user, plans = await asyncio.gather(get_user(cb.from_user.id), get_all_plans())
    await cb.answer()
    text = "💎 **Choose Your Plan**\n\nSelect a plan to see samples and pricing."
    try:
        await cb.edit_message_text(text, reply_markup=plans_list_kb(user, plans))
    except Exception:
        await client.send_message(cb.message.chat.id, text, reply_markup=plans_list_kb(user, plans))


@Client.on_callback_query(filters.regex(r"^plan:view:(\d+)$"))
async def plan_view_handler(client: Client, cb: CallbackQuery):
    plan_id = cb.matches[0].group(1)
    plan = await get_plan(plan_id)
    if not plan:
        await cb.answer("Plan not found.", show_alert=True)
        return

    await cb.answer()

    user = await get_user(cb.from_user.id)
    has_access = plan_id in owned_plans(user)

    status_line = ""
    if plan_id == user.get("current_plan") if user else False:
        status_line = "\n👑 **Current Plan**"
    elif has_access:
        status_line = "\n✅ **Subscribed**"

    text = (
        f"💎 **{plan['title']}**  —  ₹{plan['price']}{status_line}\n\n"
        f"{plan['description']}\n\n"
        "📸 _Sample previews below:_"
    )
    try:
        await cb.edit_message_text(text, reply_markup=plan_view_kb(plan_id, has_access))
    except Exception:
        await client.send_message(cb.message.chat.id, text, reply_markup=plan_view_kb(plan_id, has_access))

    # REQ-7/8/9: Send admin-curated samples only; never premium content.
    samples = await get_samples(plan_id)
    if not samples:
        await client.send_message(cb.message.chat.id, "📭 No samples uploaded for this plan yet.")
        return

    # BUG-13 FIX: FloodWait retry + delay to stay within Telegram's rate limits.
    for sample in samples:
        caption   = sample.get("caption", "")
        file_type = sample["file_type"]
        file_id   = sample["file_id"]
        for attempt in range(2):
            try:
                if file_type == "photo":
                    await client.send_photo(cb.message.chat.id, file_id, caption=caption)
                elif file_type == "video":
                    await client.send_video(cb.message.chat.id, file_id, caption=caption)
                else:
                    await client.send_document(cb.message.chat.id, file_id, caption=caption)
                break
            except FloodWait as e:
                if attempt == 0:
                    logger.warning("FloodWait %ds sending sample to %s", e.value, cb.message.chat.id)
                    await asyncio.sleep(e.value + 1)
                else:
                    logger.error("FloodWait retry failed: %s", e)
                    break
            except Exception as e:
                logger.error("Failed to send sample: %s", e)
                break
        await asyncio.sleep(0.35)


@Client.on_callback_query(filters.regex(r"^plan:getmore:(\d+)$"))
async def plan_getmore_handler(client: Client, cb: CallbackQuery):
    plan_id = cb.matches[0].group(1)
    await cb.answer()

    qr              = await get_setting("payment_qr")
    payment_details = await get_setting("payment_details") or "Payment details not configured yet."
    caption = (
        f"💰 **Payment Details**\n\n"
        f"{payment_details}\n\n"
        "After payment, tap **Enter Activation Key** below or contact admin."
    )

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
