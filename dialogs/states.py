from aiogram.fsm.state import State, StatesGroup


class StartSG(StatesGroup):
    input_email = State()


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


class HistoryOrdersSG(StatesGroup):
    orders = State()
    order_detail = State()


class CurrentOrdersSG(StatesGroup):
    orders = State()
    order_detail = State()


class CheckoutOrderSG(StatesGroup):
    select_delivery_type = State()
    input_delivery_address = State()
    confirmation = State()
    success_checkout = State()
