from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message

from bot.utils.decorators import admin_only, state_store
from bot.database.plans import get_plan, update_plan_field
from bot.keyboards.admin_kb import admin_plan_select_kb, admin_plan_edit_kb
from bot.config import config


@Client.on_callback_query(filters.regex(r"^admin:plans$"))
@admin_only
async def plans_menu_handler(client: Client, cb: CallbackQuery):
    await cb.answer()
    await cb.edit_message_text("💳 **Manage Plans**\n\nSelect a plan to edit:", reply_markup=admin_plan_select_kb("admin:planedit"))


@Client.on_callback_query(filters.regex(r"^admin:planedit:(\d+)$"))
@admin_only
async def plan_edit_menu_handler(client: Client, cb: CallbackQuery):
    plan_id = cb.matches[0].group(1)
    plan = await get_plan(plan_id)
    await cb.answer()
    text = (
        f"💳 **₹{plan_id} Plan**\n\n"
        f"Title: {plan['title']}\n"
        f"Description: {plan['description']}\n"
        f"Price: ₹{plan['price']}\n\n"
        "Choose a field to edit:"
    )
    await cb.edit_message_text(text, reply_markup=admin_plan_edit_kb(plan_id))


@Client.on_callback_query(filters.regex(r"^admin:planfield:(\d+):(title|description|price)$"))
@admin_only
async def plan_field_prompt(client: Client, cb: CallbackQuery):
    plan_id, field = cb.matches[0].group(1), cb.matches[0].group(2)
    state_store.set(cb.from_user.id, "admin_awaiting:planfield", {"plan": plan_id, "field": field})
    await cb.answer()
    await client.send_message(cb.message.chat.id, f"✏️ Send the new **{field}** for ₹{plan_id} plan now.")


def _awaiting_planfield(_, __, message: Message) -> bool:
    if not message.from_user or message.from_user.id not in config.ADMIN_IDS:
        return False
    state = state_store.get(message.from_user.id)
    return bool(state and state["step"] == "admin_awaiting:planfield")


awaiting_planfield_filter = filters.create(_awaiting_planfield)


@Client.on_message(filters.private & filters.text & awaiting_planfield_filter)
@admin_only
async def plan_field_capture(client: Client, message: Message):
    state = state_store.get(message.from_user.id)
    plan_id = state["data"]["plan"]
    field = state["data"]["field"]
    state_store.clear(message.from_user.id)

    value = message.text.strip()
    if field == "price":
        if not value.isdigit():
            await message.reply_text("❌ Price must be a whole number. Please try again from the admin panel.")
            return
        value = int(value)

    await update_plan_field(plan_id, field, value)
    await message.reply_text(f"✅ ₹{plan_id} plan **{field}** updated successfully.")
