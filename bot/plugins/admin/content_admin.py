"""
Admin content management.

REQ-31: Upload content by selecting the target plan.
REQ-32/35: Every uploaded item is indexed automatically on insert.
REQ-36/37/38 FIX: Edit caption and delete content are fully button-based
    via the Content Library section — no slash commands needed for
    daily management. The old /delcontent and /editcaption commands are
    removed; everything happens through the 📋 Content Library button in
    the admin panel.
"""
import asyncio

from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import CallbackQuery, Message

from bot.utils.decorators import admin_only, state_store
from bot.database.contents import (
    add_content, delete_content, edit_content_caption, get_content_page,
)
from bot.keyboards.admin_kb import (
    admin_plan_select_kb,
    admin_upload_category_kb,
    admin_contentlib_plan_kb,
    admin_content_item_kb,
    admin_content_del_confirm_kb,
    admin_contentlib_nav_kb,
)
from bot.utils.pagination import total_pages
from bot.config import config
from bot.utils.logger import logger


# ── Upload flow ────────────────────────────────────────────────────────────

@Client.on_callback_query(filters.regex(r"^admin:upload$"))
@admin_only
async def upload_menu_handler(client: Client, cb: CallbackQuery):
    await cb.answer()
    await cb.edit_message_text(
        "📤 **Upload Content**\n\nSelect the target plan:",
        reply_markup=admin_plan_select_kb("admin:uploadplan"),
    )


@Client.on_callback_query(filters.regex(r"^admin:uploadplan:(\d+)$"))
@admin_only
async def upload_plan_handler(client: Client, cb: CallbackQuery):
    plan_id = cb.matches[0].group(1)
    await cb.answer()
    if plan_id == "799":
        await cb.edit_message_text(
            "📤 **Upload to ₹799 Plan**\n\nSelect a category:",
            reply_markup=admin_upload_category_kb(plan_id),
        )
    else:
        state_store.set(cb.from_user.id, "admin_awaiting:content_media",
                        {"plan": plan_id, "category": None})
        await client.send_message(
            cb.message.chat.id,
            f"📤 Send the photo/video/file for **₹{plan_id} plan** now.\n"
            "Include a caption — it will be shown to subscribers.\n\n"
            "Send /cancel to abort.",
        )


@Client.on_callback_query(filters.regex(r"^admin:upload:cat:(\d+):(\w+)$"))
@admin_only
async def upload_category_handler(client: Client, cb: CallbackQuery):
    plan_id, category = cb.matches[0].group(1), cb.matches[0].group(2)
    state_store.set(cb.from_user.id, "admin_awaiting:content_media",
                    {"plan": plan_id, "category": category})
    await cb.answer()
    await client.send_message(
        cb.message.chat.id,
        f"📤 Send the photo/video/file for **₹{plan_id} — {category}** now.\n"
        "Include a caption — it will be shown to subscribers.\n\n"
        "Send /cancel to abort.",
    )


def _awaiting_content_media(_, __, message: Message) -> bool:
    if not message.from_user or message.from_user.id not in config.ADMIN_IDS:
        return False
    state = state_store.get(message.from_user.id)
    return bool(state and state["step"] == "admin_awaiting:content_media")


awaiting_content_media_filter = filters.create(_awaiting_content_media)


@Client.on_message(
    filters.private &
    (filters.photo | filters.video | filters.document) &
    awaiting_content_media_filter
)
@admin_only
async def content_media_capture(client: Client, message: Message):
    state    = state_store.get(message.from_user.id)
    plan_id  = state["data"]["plan"]
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
        plan=plan_id, category=category,
        file_id=file_id, file_type=file_type, caption=caption,
        preview_file_id=None, preview_caption=None, thumbnail=None,
        uploaded_by=message.from_user.id,
    )
    cat_label = f" / {category}" if category else ""
    await message.reply_text(
        f"✅ Content added to **₹{plan_id}{cat_label}** plan.\n"
        "It is now indexed and visible to subscribers.",
    )


# ── Content Library (browse / edit / delete existing content) ──────────────

@Client.on_callback_query(filters.regex(r"^admin:contentlib$"))
@admin_only
async def contentlib_menu_handler(client: Client, cb: CallbackQuery):
    await cb.answer()
    await cb.edit_message_text(
        "📋 **Content Library**\n\n"
        "Browse, edit captions, or delete existing content.\n"
        "Select a plan:",
        reply_markup=admin_contentlib_plan_kb(),
    )


@Client.on_callback_query(filters.regex(r"^admin:clplan:(\d+)$"))
@admin_only
async def contentlib_plan_handler(client: Client, cb: CallbackQuery):
    plan_id = cb.matches[0].group(1)
    await cb.answer()
    # Delegate to page 1.
    await _show_contentlib_page(client, cb.message.chat.id, plan_id, page=1)


@Client.on_callback_query(filters.regex(r"^admin:contentlib:(\d+):(\d+)$"))
@admin_only
async def contentlib_page_handler(client: Client, cb: CallbackQuery):
    plan_id = cb.matches[0].group(1)
    page    = int(cb.matches[0].group(2))
    await cb.answer()
    await _show_contentlib_page(client, cb.message.chat.id, plan_id, page=page)


async def _show_contentlib_page(client: Client, chat_id: int, plan_id: str, page: int):
    items, total = await get_content_page(plan_id, page, category=None)
    pages = total_pages(total)

    if not items:
        await client.send_message(
            chat_id,
            f"📭 No content for ₹{plan_id} plan yet.\n\nUse 📤 Upload Content to add items.",
        )
        return

    await client.send_message(
        chat_id,
        f"📋 **₹{plan_id} Plan — Content Library**\n"
        f"Page {page} of {pages}  ({total} item{'' if total == 1 else 's'} total)\n\n"
        "Each item has ✏️ Edit Caption and 🗑 Delete buttons.",
    )

    for item in items:
        oid     = str(item["_id"])
        caption = item.get("caption") or "(no caption)"
        preview = caption[:60] + "…" if len(caption) > 60 else caption
        kb      = admin_content_item_kb(oid, plan_id, page)

        try:
            ft = item["file_type"]
            if ft == "photo":
                await client.send_photo(chat_id, item["file_id"], caption=preview, reply_markup=kb)
            elif ft == "video":
                await client.send_video(chat_id, item["file_id"], caption=preview, reply_markup=kb)
            else:
                await client.send_document(chat_id, item["file_id"], caption=preview, reply_markup=kb)
        except Exception as e:
            logger.warning("Could not resend content item %s: %s", oid, e)
            await client.send_message(
                chat_id,
                f"[{item['file_type']}] {preview}",
                reply_markup=kb,
            )
        await asyncio.sleep(0.3)

    await client.send_message(
        chat_id,
        f"📄 Page navigation — ₹{plan_id} plan",
        reply_markup=admin_contentlib_nav_kb(plan_id, page, pages),
    )


# ── Edit Caption ────────────────────────────────────────────────────────────

@Client.on_callback_query(filters.regex(r"^admin:clitem:edit:([a-f0-9]{24}):(\d+):(\d+)$"))
@admin_only
async def contentlib_edit_prompt(client: Client, cb: CallbackQuery):
    oid     = cb.matches[0].group(1)
    plan_id = cb.matches[0].group(2)
    page    = int(cb.matches[0].group(3))
    state_store.set(cb.from_user.id, "admin_awaiting:content_edit",
                    {"content_id": oid, "plan_id": plan_id, "page": page})
    await cb.answer()
    await client.send_message(
        cb.message.chat.id,
        "✏️ **Edit Caption**\n\nSend the new caption text for this item now.\n\nSend /cancel to abort.",
    )


def _awaiting_content_edit(_, __, message: Message) -> bool:
    if not message.from_user or message.from_user.id not in config.ADMIN_IDS:
        return False
    state = state_store.get(message.from_user.id)
    return bool(state and state["step"] == "admin_awaiting:content_edit")


awaiting_content_edit_filter = filters.create(_awaiting_content_edit)


@Client.on_message(filters.private & filters.text & awaiting_content_edit_filter)
@admin_only
async def contentlib_edit_capture(client: Client, message: Message):
    state      = state_store.get(message.from_user.id)
    content_id = state["data"]["content_id"]
    plan_id    = state["data"]["plan_id"]
    page       = state["data"]["page"]
    state_store.clear(message.from_user.id)

    new_caption = message.text.strip()
    ok = await edit_content_caption(content_id, new_caption)
    if ok:
        await message.reply_text(
            "✅ Caption updated successfully.\n\n"
            f"Tap below to return to the library.",
            reply_markup=admin_contentlib_nav_kb(plan_id, page, 1),
        )
    else:
        await message.reply_text("❌ Content item not found — it may have been deleted already.")


# ── Delete Content ──────────────────────────────────────────────────────────

@Client.on_callback_query(filters.regex(r"^admin:clitem:del:([a-f0-9]{24}):(\d+):(\d+)$"))
@admin_only
async def contentlib_del_confirm(client: Client, cb: CallbackQuery):
    oid     = cb.matches[0].group(1)
    plan_id = cb.matches[0].group(2)
    page    = int(cb.matches[0].group(3))
    await cb.answer()
    # Edit the item's reply_markup to show confirm buttons directly on that message.
    try:
        await cb.message.edit_reply_markup(admin_content_del_confirm_kb(oid, plan_id, page))
    except Exception:
        await client.send_message(
            cb.message.chat.id,
            "⚠️ Confirm deletion of this item?",
            reply_markup=admin_content_del_confirm_kb(oid, plan_id, page),
        )


@Client.on_callback_query(filters.regex(r"^admin:clitem:del:yes:([a-f0-9]{24}):(\d+):(\d+)$"))
@admin_only
async def contentlib_del_execute(client: Client, cb: CallbackQuery):
    oid     = cb.matches[0].group(1)
    plan_id = cb.matches[0].group(2)
    page    = int(cb.matches[0].group(3))

    ok = await delete_content(oid)
    if ok:
        await cb.answer("🗑 Deleted.", show_alert=False)
        try:
            await cb.message.delete()
        except Exception:
            pass
        await client.send_message(
            cb.message.chat.id,
            "✅ Item deleted successfully.",
            reply_markup=admin_contentlib_nav_kb(plan_id, page, 1),
        )
    else:
        await cb.answer("❌ Item not found — already deleted.", show_alert=True)
