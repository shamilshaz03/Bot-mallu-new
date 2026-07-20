from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message

from bot.utils.decorators import admin_only, state_store
from bot.database.contents import add_content, delete_content, edit_content_caption
from bot.keyboards.admin_kb import admin_plan_select_kb, admin_upload_category_kb
from bot.config import config


@Client.on_callback_query(filters.regex(r"^admin:upload$"))
@admin_only
async def upload_menu_handler(client: Client, cb: CallbackQuery):
    await cb.answer()
    await cb.edit_message_text("📤 **Upload Content**\n\nSelect target plan:", reply_markup=admin_plan_select_kb("admin:uploadplan"))


@Client.on_callback_query(filters.regex(r"^admin:uploadplan:(\d+)$"))
@admin_only
async def upload_plan_handler(client: Client, cb: CallbackQuery):
    plan_id = cb.matches[0].group(1)
    await cb.answer()

    if plan_id == "799":
        await cb.edit_message_text("Select category:", reply_markup=admin_upload_category_kb(plan_id))
    else:
        state_store.set(cb.from_user.id, "admin_awaiting:content_media", {"plan": plan_id, "category": None})
        await client.send_message(
            cb.message.chat.id,
            f"📤 Send the content (photo/video/file) for ₹{plan_id} plan now.\nUse the caption for the item's caption.",
        )


@Client.on_callback_query(filters.regex(r"^admin:upload:cat:(\d+):(\w+)$"))
@admin_only
async def upload_category_handler(client: Client, cb: CallbackQuery):
    plan_id, category = cb.matches[0].group(1), cb.matches[0].group(2)
    state_store.set(cb.from_user.id, "admin_awaiting:content_media", {"plan": plan_id, "category": category})
    await cb.answer()
    await client.send_message(
        cb.message.chat.id,
        f"📤 Send the content (photo/video/file) for ₹{plan_id} plan / {category} now.\nUse the caption for the item's caption.",
    )


def _awaiting_content_media(_, __, message: Message) -> bool:
    if not message.from_user or message.from_user.id not in config.ADMIN_IDS:
        return False
    state = state_store.get(message.from_user.id)
    return bool(state and state["step"] == "admin_awaiting:content_media")


awaiting_content_media_filter = filters.create(_awaiting_content_media)


@Client.on_message(filters.private & (filters.photo | filters.video | filters.document) & awaiting_content_media_filter)
@admin_only
async def content_media_capture(client: Client, message: Message):
    state = state_store.get(message.from_user.id)
    plan_id = state["data"]["plan"]
    category = state["data"]["category"]
    state_store.clear(message.from_user.id)

    if message.photo:
        file_id, file_type = message.photo.file_id, "photo"
    elif message.video:
        file_id, file_type = message.video.file_id, "video"
    else:
        file_id, file_type = message.document.file_id, "document"

    caption = message.caption or ""

    await add_content(
        plan=plan_id,
        category=category,
        file_id=file_id,
        file_type=file_type,
        caption=caption,
        preview_file_id=None,
        preview_caption=None,
        thumbnail=None,
        uploaded_by=message.from_user.id,
    )
    await message.reply_text(f"✅ Content added to ₹{plan_id} plan" + (f" / {category}" if category else "") + ". It's now indexed and live.")


# ---- Delete / edit content by replying with a command ----

@Client.on_message(filters.command("delcontent") & filters.private)
@admin_only
async def delete_content_command(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("Usage: `/delcontent <content_id>`")
        return
    content_id = message.command[1]
    ok = await delete_content(content_id)
    await message.reply_text("✅ Content deleted." if ok else "❌ Content not found.")


@Client.on_message(filters.command("editcaption") & filters.private)
@admin_only
async def edit_caption_command(client: Client, message: Message):
    if len(message.command) < 3:
        await message.reply_text("Usage: `/editcaption <content_id> <new caption text>`")
        return
    content_id = message.command[1]
    new_caption = message.text.split(None, 2)[2]
    ok = await edit_content_caption(content_id, new_caption)
    await message.reply_text("✅ Caption updated." if ok else "❌ Content not found.")
