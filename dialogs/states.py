from aiogram.fsm.state import State, StatesGroup


class StartSG(StatesGroup):
    start = State()


class MenuSG(StatesGroup):
    menu = State()


class ProductsSG(StatesGroup):
    categories = State()
    products = State()
    product_detail = State()


class CartsSG(StatesGroup):
    carts = State()
    cart_item = State()


class ProfileSG(StatesGroup):
    profile = State()


class OrdersSG(StatesGroup):
    orders = State()
    order_detail = State()
