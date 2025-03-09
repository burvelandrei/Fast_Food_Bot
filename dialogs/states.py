from aiogram.fsm.state import State, StatesGroup


class StartSG(StatesGroup):
    start = State()


class MenuSG(StatesGroup):
    menu = State()


class ProductsSG(StatesGroup):
    categories = State()
    products = State()
    product_detail = State()
