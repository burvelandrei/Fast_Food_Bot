from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, Dialog, Window, StartMode
from aiogram_dialog.widgets.text import Const, Format, List, Case
from aiogram_dialog.widgets.input import TextInput, ManagedTextInput
from aiogram_dialog.widgets.kbd import (
    SwitchTo,
    Button,
    Start,
)
from dialogs.states import CheckoutOrderSG, MenuSG
from services.api_client import APIClient, APIError
from db.operations import UserDO


# Хэндлер обрабатывающий выбор способа доставки
async def select_delivery_type_button(
    callback: CallbackQuery, widget: Button, dialog_manager: DialogManager
):
    delivery_type = widget.widget_id
    dialog_manager.dialog_data["delivery_type"] = delivery_type
    dialog_manager.dialog_data["delivery_address"] = None
    if delivery_type == "pickup":
        await dialog_manager.switch_to(state=CheckoutOrderSG.confirmation)
    elif delivery_type == "courier":
        await dialog_manager.switch_to(state=CheckoutOrderSG.input_delivery_address)


# Хэндлер для обработки корректного адресса
async def correct_delivery_address(
    message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str
):
    dialog_manager.dialog_data["delivery_address"] = text
    await dialog_manager.switch_to(state=CheckoutOrderSG.confirmation)


# Хэндлер кнопки оформления заказа
async def confirmation_order_button(
    callback: CallbackQuery, widget: Button, dialog_manager: DialogManager
):
    tg_id = str(dialog_manager.event.from_user.id)
    session = dialog_manager.middleware_data["session"]
    user = await UserDO.get_by_tg_id(tg_id=tg_id, session=session)
    delivery_type = dialog_manager.dialog_data["delivery_type"]
    delivery_address = dialog_manager.dialog_data["delivery_address"]
    data = {
        "delivery_type": delivery_type,
        "delivery_address": delivery_address,
    }
    try:
        async with APIClient(user.email) as api:
            await api.post("/orders/confirmation/", data=data)
            await dialog_manager.switch_to(state=CheckoutOrderSG.success_checkout)
    except APIError:
        error_message = "Не удалось оформить заказ."
        await callback.answer(f"⚠️ Ошибка: {error_message}")


# Геттер для получения корзины для отображения в финальном подтверждении
async def confirmation_order_getter(dialog_manager: DialogManager, **kwargs):
    tg_id = str(dialog_manager.event.from_user.id)
    session = dialog_manager.middleware_data["session"]
    user = await UserDO.get_by_tg_id(tg_id=tg_id, session=session)
    delivery_type = dialog_manager.dialog_data["delivery_type"]
    delivery_address = dialog_manager.dialog_data["delivery_address"]
    try:
        async with APIClient(user.email) as api:
            order = await api.get(f"/carts/")
            return {
                "cart_items": order["cart_items"],
                "total_amount": order["total_amount"],
                "delivery_type": delivery_type,
                "delivery_address": delivery_address,
                "error_message": None,
            }
    except APIError:
        return {
            "cart_items": [],
            "total_amount": 0,
            "delivery_type": "-",
            "delivery_address": "-",
            "error_message": "Информация о заказе временно недоступна",
        }


# Окно выбора способа доставки
select_delivery_type = Window(
    Const("Выберите способ доставки:"),
    Button(
        text=Const("🚶Самовывоз"),
        id="pickup",
        on_click=select_delivery_type_button,
    ),
    Button(
        text=Const("🚚 Доставка"),
        id="courier",
        on_click=select_delivery_type_button,
    ),
    Start(
        text=Const("🔙 Назад в Меню!"),
        id="back_to_menu",
        state=MenuSG.menu,
        mode=StartMode.RESET_STACK,
    ),
    state=CheckoutOrderSG.select_delivery_type,
)


# Окно ввода адресса доставки
input_delivery_type = Window(
    Const("Введите адрес доставки"),
    TextInput(
        id="delivery_address_input",
        on_success=correct_delivery_address,
    ),
    SwitchTo(
        text=Const("🔙 Назад"),
        id="back_to_select_delivery_type",
        state=CheckoutOrderSG.select_delivery_type,
    ),
    Start(
        text=Const("🔙 Назад в Меню!"),
        id="back_to_menu",
        state=MenuSG.menu,
        mode=StartMode.RESET_STACK,
    ),
    state=CheckoutOrderSG.input_delivery_address,
)


# Окно финального подтверждения заказа
confirmation_order_window = Window(
    Format("📜 Состав заказа:"),
    Format("{error_message}", when="error_message"),
    List(
        Format(
            """
            - {item[product][name]} {item[product][size_name]} x {item[quantity]} шт. |  {item[total_price]} руб."""
        ),
        items="cart_items",
    ),
    Format("\n💰  Итоговая сумма: {total_amount} руб.\n"),
    Case(
        {
            "pickup": Const("Способ доставки: 🚶 Самовывоз"),
            "courier": Const("Способ доставки: 🚚 Доставка курьером"),
        },
        selector=lambda data, *_: data["delivery_type"],
    ),
    Format(
        "Адрес для доставки: {delivery_address}",
        when="delivery_address",
    ),
    Button(
        Const("✅ Подтвердить заказ"),
        id="confirmation_order",
        on_click=confirmation_order_button,
    ),
    SwitchTo(
        text=Const("🔙 Поменять адресс"),
        id="back_to_input_delivery_address",
        when="delivery_address",
        state=CheckoutOrderSG.input_delivery_address,
    ),
    Start(
        text=Const("🔙 Назад в Меню!"),
        id="back_to_menu",
        state=MenuSG.menu,
        mode=StartMode.RESET_STACK,
    ),
    getter=confirmation_order_getter,
    state=CheckoutOrderSG.confirmation,
)


# Окно для вывода успешного результата оформления заказа
success_checkout = Window(
    Const("🎉 Заказ успешно оформлен"),
    Start(
        text=Const("🔙 Назад в Меню!"),
        id="back_to_menu",
        state=MenuSG.menu,
        mode=StartMode.RESET_STACK,
    ),
    state=CheckoutOrderSG.success_checkout,
)

dialog = Dialog(
    select_delivery_type,
    input_delivery_type,
    confirmation_order_window,
    success_checkout,
)
