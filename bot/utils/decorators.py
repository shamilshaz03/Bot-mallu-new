from functools import wraps
from pyrogram.types import Message, CallbackQuery
from bot.config import config


def admin_only(func):
    """Reject non-admin users before hitting handler logic. Works for both Message and CallbackQuery."""
    @wraps(func)
    async def wrapper(client, update, *args, **kwargs):
        user_id = update.from_user.id if update.from_user else None
        if user_id not in config.ADMIN_IDS:
            if isinstance(update, CallbackQuery):
                await update.answer("⛔ You are not authorized to use this.", show_alert=True)
            elif isinstance(update, Message):
                await update.reply_text("⛔ You are not authorized to use this command.")
            return
        return await func(client, update, *args, **kwargs)
    return wrapper


class StateStore:
    """
    Minimal in-memory conversation state for multi-step admin flows
    (upload content, edit plan, broadcast, etc). Pyrogram has no built-in
    FSM, so a simple dict keyed by admin user_id is enough for this bot's
    single-process deployment model on Koyeb.
    """
    def __init__(self):
        self._states: dict[int, dict] = {}

    def set(self, user_id: int, step: str, data: dict | None = None):
        self._states[user_id] = {"step": step, "data": data or {}}

    def get(self, user_id: int) -> dict | None:
        return self._states.get(user_id)

    def update_data(self, user_id: int, **kwargs):
        if user_id in self._states:
            self._states[user_id]["data"].update(kwargs)

    def clear(self, user_id: int):
        self._states.pop(user_id, None)

    def is_in_state(self, user_id: int, step_prefix: str) -> bool:
        state = self._states.get(user_id)
        return bool(state and state["step"].startswith(step_prefix))


state_store = StateStore()
