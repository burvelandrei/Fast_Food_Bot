from aiogram.fsm.state import State, StatesGroup


class StartState(StatesGroup):
    start = State()


class MenuState(StatesGroup):
    menu = State()


class ProductsState(StatesGroup):
    categories = State()
    products = State()
    product_detail = State()
