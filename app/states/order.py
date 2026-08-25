from aiogram.fsm.state import State, StatesGroup

class OrderState(StatesGroup):
    phone = State()
    address = State()