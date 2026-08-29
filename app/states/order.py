
from aiogram.fsm.state import State, StatesGroup


class OrderState(StatesGroup):
    promo = State()
    phone = State()
    address = State()