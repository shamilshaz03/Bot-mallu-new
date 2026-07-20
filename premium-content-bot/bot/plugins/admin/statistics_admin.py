from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from bot.utils.decorators import admin_only
from bot.database.statistics import build_statistics_report
from bot.keyboards.admin_kb import admin_back_kb


@Client.on_callback_query(filters.regex(r"^admin:stats$"))
@admin_only
async def stats_handler(client: Client, cb: CallbackQuery):
    await cb.answer()
    report = await build_statistics_report()
    await cb.edit_message_text(report, reply_markup=admin_back_kb())
