from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const
from aiogram_dialog.widgets.kbd import Start
from dialogs.states import MenuSG, ProductsSG, OrdersSG, CartsSG


menu_window = Window(
    Const("📋 Меню"),
    Start(
        Const("🍔 Список продуктов"),
        id="products",
        state=ProductsSG.categories,
    ),
    Start(
        Const("🛒 Корзина"),
        id="carts",
        state=CartsSG.carts,
    ),
    Start(
        Const("📜 История заказов"),
        id="history_orders",
        state=OrdersSG.orders,
    ),
    state=MenuSG.menu,
)


dialog = Dialog(menu_window)
