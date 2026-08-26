from aiogram.fsm.state import State, StatesGroup


class AddProduct(StatesGroup):
    category = State()
    name = State()
    description = State()
    price = State()


class AddCategory(StatesGroup):
    name = State()