from aiogram.fsm.state import State, StatesGroup


class AddProduct(StatesGroup):
    category = State()
    name = State()
    description = State()
    price = State()


class AddCategory(StatesGroup):
    name = State()

class AddShop(StatesGroup):
    name = State()
    owner_id = State()
class EditProduct(StatesGroup):
    price = State()
    quantity = State()