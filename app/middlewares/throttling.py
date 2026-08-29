import time
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, limit: float = 0.7):
        self.limit = limit
        self.last_call = {}

    async def __call__(self, handler, event, data):
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id

        if user_id:
            now = time.monotonic()
            last = self.last_call.get(user_id, 0)
            if now - last < self.limit:
                if isinstance(event, CallbackQuery):
                    await event.answer("Iltimos, biroz sekinroq bosing 🙂", show_alert=False)
                return
            self.last_call[user_id] = now

        return await handler(event, data)