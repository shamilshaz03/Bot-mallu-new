from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot.utils.decorators import admin_only, state_store
from bot.database.samples import add_sample, get_samples, delete_sample
from bot.keyboards.admin_kb import admin_plan_select_kb
from bot.config import config


def samples_plan_menu_kb(plan_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Sample", callback_data=f"admin:samples:add:{plan_id}")],
        [InlineKeyboardButton("📄 List / Delete Samples", callback_data=f"admin:samples:list:{plan_id}")],
        [InlineKeyboardButton("⬅ Back", callback_data="admin:samples")],
    ])


@Client.on_callback_query(filters.regex(r"^admin:samples$"))
@admin_only
async def samples_menu_handler(client: Client, cb: CallbackQuery):
    await cb.answer()
    await cb.edit_message_text("🎁 **Manage Samples**\n\nSelect a plan:", reply_markup=admin_plan_select_kb("admin:samplesplan"))


@Client.on_callback_query(filters.regex(r"^admin:samplesplan:(\d+)$"))
@admin_only
async def samples_plan_handler(client: Client, cb: CallbackQuery):
    plan_id = cb.matches[0].group(1)
    await cb.answer()
    await cb.edit_message_text(f"🎁 **Samples for ₹{plan_id} Plan**", reply_markup=samples_plan_menu_kb(plan_id))


@Client.on_callback_query(filters.regex(r"^admin:samples:add:(\d+)$"))
@admin_only
async def samples_add_prompt(client: Client, cb: CallbackQuery):
    plan_id = cb.matches[0].group(1)
    state_store.set(cb.from_user.id, "admin_awaiting:sample_media", {"plan": plan_id})
    await cb.answer()
    await client.send_message(
        cb.message.chat.id,
        f"📤 Send the sample photo/video/file for ₹{plan_id} plan now.\n"
        "Send the caption as the media caption (or leave blank).",
    )


def _awaiting_sample_media(_, __, message: Message) -> bool:
    if not message.from_user or message.from_user.id not in config.ADMIN_IDS:
        return False
    state = state_store.get(message.from_user.id)
    return bool(state and state["step"] == "admin_awaiting:sample_media")


awaiting_sample_media_filter = filters.create(_awaiting_sample_media)


@Client.on_message(filters.private & (filters.photo | filters.video | filters.document) & awaiting_sample_media_filter)
@admin_only
async def samples_add_capture(client: Client, message: Message):
    state = state_store.get(message.from_user.id)
    plan_id = state["data"]["plan"]
    state_store.clear(message.from_user.id)

    if message.photo:
        file_id, file_type = message.photo.file_id, "photo"
    elif message.video:
        file_id, file_type = message.video.file_id, "video"
    else:
        file_id, file_type = message.document.file_id, "document"

    caption = message.caption or ""
    await add_sample(plan_id, file_id, file_type, caption, message.from_user.id)
    await message.reply_text(f"✅ Sample added to ₹{plan_id} plan.")


@Client.on_callback_query(filters.regex(r"^admin:samples:list:(\d+)$"))
@admin_only
async def samples_list_handler(client: Client, cb: CallbackQuery):
    plan_id = cb.matches[0].group(1)
    samples = await get_samples(plan_id)
    await cb.answer()

    if not samples:
        await client.send_message(cb.message.chat.id, f"No samples yet for ₹{plan_id} plan.")
        return

    for s in samples:
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🗑 Delete", callback_data=f"admin:samples:del:{s['_id']}:{plan_id}")]])
        caption = s.get("caption", "") or "(no caption)"
        await client.send_message(cb.message.chat.id, f"Sample: {caption}", reply_markup=kb)


@Client.on_callback_query(filters.regex(r"^admin:samples:del:(\w+):(\d+)$"))
@admin_only
async def samples_delete_handler(client: Client, cb: CallbackQuery):
    sample_id, plan_id = cb.matches[0].group(1), cb.matches[0].group(2)
    await delete_sample(sample_id)
    await cb.answer("Deleted.")
    try:
        await cb.message.delete()
    except Exception:
        pass
