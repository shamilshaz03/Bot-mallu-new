from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from bot.utils.decorators import admin_only
from bot.database.keys import create_keys, get_unused_keys, get_used_keys, delete_unused_keys
from bot.keyboards.admin_kb import admin_keys_menu_kb, admin_plan_select_kb, admin_key_count_kb, confirm_kb
from bot.utils.logger import logger


@Client.on_callback_query(filters.regex(r"^admin:keys$"))
@admin_only
async def keys_menu_handler(client: Client, cb: CallbackQuery):
    await cb.answer()
    await cb.edit_message_text("🔑 **Activation Keys**", reply_markup=admin_keys_menu_kb())


@Client.on_callback_query(filters.regex(r"^admin:keys:gen$"))
@admin_only
async def keys_gen_plan_handler(client: Client, cb: CallbackQuery):
    await cb.answer()
    await cb.edit_message_text("Select the plan to generate keys for:", reply_markup=admin_plan_select_kb("admin:keys:genplan"))


@Client.on_callback_query(filters.regex(r"^admin:keys:genplan:(\d+)$"))
@admin_only
async def keys_gen_count_handler(client: Client, cb: CallbackQuery):
    plan_id = cb.matches[0].group(1)
    await cb.answer()
    await cb.edit_message_text(f"How many ₹{plan_id} keys do you want to generate?", reply_markup=admin_key_count_kb(plan_id))


@Client.on_callback_query(filters.regex(r"^admin:keys:doGen:(\d+):(\d+)$"))
@admin_only
async def keys_do_gen_handler(client: Client, cb: CallbackQuery):
    plan_id, count = cb.matches[0].group(1), int(cb.matches[0].group(2))
    await cb.answer("Generating...")

    keys = await create_keys(plan_id, count, cb.from_user.id)
    logger.info("Admin %s generated %d keys for plan %s", cb.from_user.id, len(keys), plan_id)

    text = f"✅ Generated {len(keys)} key(s) for ₹{plan_id} plan:\n\n" + "\n".join(f"`{k}`" for k in keys)
    await client.send_message(cb.message.chat.id, text)


@Client.on_callback_query(filters.regex(r"^admin:keys:unused$"))
@admin_only
async def keys_unused_handler(client: Client, cb: CallbackQuery):
    await cb.answer()
    keys = await get_unused_keys(limit=100)
    if not keys:
        await client.send_message(cb.message.chat.id, "No unused keys.")
        return
    lines = [f"`{k['key']}` — ₹{k['plan']}" for k in keys]
    await client.send_message(cb.message.chat.id, "🔑 **Unused Keys (latest 100):**\n\n" + "\n".join(lines))


@Client.on_callback_query(filters.regex(r"^admin:keys:used$"))
@admin_only
async def keys_used_handler(client: Client, cb: CallbackQuery):
    await cb.answer()
    keys = await get_used_keys(limit=100)
    if not keys:
        await client.send_message(cb.message.chat.id, "No used keys yet.")
        return
    lines = [f"`{k['key']}` — ₹{k['plan']} — used by `{k['used_by']}`" for k in keys]
    await client.send_message(cb.message.chat.id, "🔓 **Used Keys (latest 100):**\n\n" + "\n".join(lines))


@Client.on_callback_query(filters.regex(r"^admin:keys:delunused$"))
@admin_only
async def keys_delunused_confirm_handler(client: Client, cb: CallbackQuery):
    await cb.answer()
    await cb.edit_message_text(
        "⚠️ Delete ALL unused keys across all plans? This cannot be undone.",
        reply_markup=confirm_kb("admin:keys:delunused:yes", "admin:keys"),
    )


@Client.on_callback_query(filters.regex(r"^admin:keys:delunused:yes$"))
@admin_only
async def keys_delunused_handler(client: Client, cb: CallbackQuery):
    count = await delete_unused_keys()
    await cb.answer(f"Deleted {count} keys.", show_alert=True)
    await cb.edit_message_text("🔑 **Activation Keys**", reply_markup=admin_keys_menu_kb())
