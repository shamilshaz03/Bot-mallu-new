from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery

from bot.utils.decorators import admin_only
from bot.database.statistics import build_statistics_report
from bot.keyboards.admin_kb import admin_back_kb


@Client.on_callback_query(filters.regex(r"^admin:stats$"))
@admin_only
async def stats_handler(client: Client, cb: CallbackQuery):
    await cb.answer()
    report = await build_statistics_report()
    # BUG-12 FIX: parse_mode=MARKDOWN so **bold** renders correctly.
    await cb.edit_message_text(report, reply_markup=admin_back_kb(), parse_mode=ParseMode.MARKDOWN)
