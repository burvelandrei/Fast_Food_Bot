from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const
from aiogram_dialog.widgets.kbd import Start
from dialogs.states import MenuSG, ProductsSG, CartsSG, ProfileSG


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
        Const("👤 Профиль"),
        id="profile",
        state=ProfileSG.profile,
    ),
    state=MenuSG.menu,
)


dialog = Dialog(menu_window)
