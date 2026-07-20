"""
Premium content feed for subscribed users.

REQ-26/27: 10 items per page, fast stable pagination (compound index).
REQ-28: ₹199/₹299 show mixed feed (no category filter).
REQ-29/30: Category browsing (Videos/Photos/Files) only for ₹799.
BUG-13 FIX: FloodWait retry + 0.35 s inter-item delay.
"""
import asyncio

from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import CallbackQuery

from bot.database.users import get_user, owned_plans
from bot.database.contents import get_content_page
from bot.keyboards.user_kb import content_nav_kb
from bot.utils.pagination import total_pages
from bot.strings import NO_CONTENT_YET
from bot.utils.logger import logger


async def _user_can_access(user_id: int, plan_id: str) -> bool:
    user = await get_user(user_id)
    return plan_id in owned_plans(user)


async def _send_item(client: Client, chat_id: int, item: dict) -> None:
    """Send one content item with FloodWait retry."""
    caption   = item.get("caption", "")
    file_type = item["file_type"]
    file_id   = item["file_id"]
    for attempt in range(2):
        try:
            if file_type == "photo":
                await client.send_photo(chat_id, file_id, caption=caption)
            elif file_type == "video":
                await client.send_video(chat_id, file_id, caption=caption)
            else:
                await client.send_document(chat_id, file_id, caption=caption)
            return
        except FloodWait as e:
            if attempt == 0:
                logger.warning("FloodWait %ds sending content to %s", e.value, chat_id)
                await asyncio.sleep(e.value + 1)
            else:
                logger.error("FloodWait retry failed for chat %s: %s", chat_id, e)
        except Exception as e:
            logger.error("Failed to send content item to %s: %s", chat_id, e)
            return


async def _render_feed(client: Client, chat_id: int, plan_id: str, page: int, category: str | None):
    items, total = await get_content_page(plan_id, page, category)
    pages = total_pages(total)

    if not items:
        await client.send_message(chat_id, NO_CONTENT_YET,
                                  reply_markup=content_nav_kb(plan_id, 1, 1, category))
        return

    for item in items:
        await _send_item(client, chat_id, item)
        await asyncio.sleep(0.35)   # BUG-13 FIX: gentle rate limiting between sends

    await client.send_message(
        chat_id,
        f"📄 **Page {page} of {pages}**  —  {total} item(s) total",
        reply_markup=content_nav_kb(plan_id, page, pages, category),
    )


@Client.on_callback_query(filters.regex(r"^feed:start:(\d+)$"))
async def feed_start_handler(client: Client, cb: CallbackQuery):
    plan_id = cb.matches[0].group(1)
    if not await _user_can_access(cb.from_user.id, plan_id):
        await cb.answer("You don't have access to this plan yet.", show_alert=True)
        return
    await cb.answer()
    await _render_feed(client, cb.message.chat.id, plan_id, page=1, category=None)


@Client.on_callback_query(filters.regex(r"^feed:page:(\d+):(\d+):(\S+)$"))
async def feed_page_handler(client: Client, cb: CallbackQuery):
    plan_id  = cb.matches[0].group(1)
    page     = int(cb.matches[0].group(2))
    cat_raw  = cb.matches[0].group(3)
    category = None if cat_raw == "-" else cat_raw

    if not await _user_can_access(cb.from_user.id, plan_id):
        await cb.answer("You don't have access to this plan yet.", show_alert=True)
        return
    await cb.answer()
    await _render_feed(client, cb.message.chat.id, plan_id, page=page, category=category)


@Client.on_callback_query(filters.regex(r"^feed:cat:(\d+):(\w+)$"))
async def feed_category_handler(client: Client, cb: CallbackQuery):
    plan_id  = cb.matches[0].group(1)
    category = cb.matches[0].group(2)

    # REQ-29/30: category browsing is exclusive to the ₹799 plan.
    if plan_id != "799":
        await cb.answer("Category browsing is only available on the ₹799 plan.", show_alert=True)
        return
    if not await _user_can_access(cb.from_user.id, plan_id):
        await cb.answer("You don't have access to this plan yet.", show_alert=True)
        return
    await cb.answer()
    await _render_feed(client, cb.message.chat.id, plan_id, page=1, category=category)
