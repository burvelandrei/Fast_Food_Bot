from datetime import datetime, timedelta
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, Dialog, Window
from aiogram_dialog.widgets.text import Const, Format, Case, List
from aiogram_dialog.widgets.kbd import (
    SwitchTo,
    Button,
    Select,
    Cancel,
    ScrollingGroup,
    Group,
)
from dialogs.states import HistoryOrdersSG
from services.api_client import APIClient, APIError
from db.operations import UserDO


# Функция для форматирования даты и времени в читаемый формат
def formatted_date(date: str):
    dt = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S")
    formatted_date = dt.strftime("%d.%m.%Y %H:%M")
    return formatted_date


# Хэндлер обработки нажотой кнопки выполненного заказа
async def history_order_button(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
):
    dialog_manager.dialog_data["order_id"] = item_id
    await dialog_manager.switch_to(state=HistoryOrdersSG.order_detail)


# Хэндлер для повтора заказа и добавления в корзину
async def repeat_order(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    order_id = dialog_manager.dialog_data["order_id"]
    tg_id = str(dialog_manager.event.from_user.id)
    session = dialog_manager.middleware_data["session"]
    user = await UserDO.get_by_tg_id(tg_id=tg_id, session=session)

    try:
        async with APIClient(user.email) as api:
            await api.post(f"/orders/repeat/{order_id}/")
            await callback.answer("Товары из заказа добавлены в корзину!")
    except APIError:
        await callback.answer("Ошибка при добавлении товаров в корзину.")


# Геттер для получения списка истории заказов и передачи в окно
async def history_orders_getter(dialog_manager: DialogManager, **kwargs):
    tg_id = str(dialog_manager.event.from_user.id)
    session = dialog_manager.middleware_data["session"]
    user = await UserDO.get_by_tg_id(tg_id=tg_id, session=session)
    try:
        async with APIClient(user.email) as api:
            orders = await api.get("/orders/?status=completed")
            for order in orders:
                created_at_moscow = order.get("created_at_moscow")
                order["created_at_moscow"] = formatted_date(created_at_moscow)
    except APIError:
        orders = None
    error_message = "История заказов временно недоступна." if orders is None else None
    return {"orders": orders, "error_message": error_message}


# Геттер для получения выполненного заказа по id и передачи в окно
async def history_order_detail_getter(dialog_manager: DialogManager, **kwargs):
    order_id = dialog_manager.dialog_data["order_id"]
    tg_id = str(dialog_manager.event.from_user.id)
    session = dialog_manager.middleware_data["session"]
    user = await UserDO.get_by_tg_id(tg_id=tg_id, session=session)
    try:
        async with APIClient(user.email) as api:
            order = await api.get(f"/orders/{order_id}/")
            return {
                "user_order_id": order["user_order_id"],
                "order_items": order["order_items"],
                "created_at_moscow": formatted_date(order["created_at_moscow"]),
                "total_amount": order["total_amount"],
                "delivery_type": order["delivery"]["delivery_type"],
                "delivery_address": order["delivery"]["delivery_address"],
                "error_message": None,
            }
    except APIError:
        return {
            "user_order_id": "-",
            "order_items": [],
            "created_at_moscow": "-",
            "total_amount": 0,
            "delivery_type": "-",
            "delivery_address": "-",
            "error_message": "Информация о заказе временно недоступна",
        }


# Окно отображения истории заказаов пользователя
history_orders_window = Window(
    # если заказов выводим то что нет заказов
    Case(
        {
            "True": Format("У вас пока нет выполненных заказов 😔"),
            "False": Format("📋 Выберите заказ для просмотра:"),
        },
        selector=lambda data, *_: str(not bool(data["orders"])),
        when=lambda data, *_: data["orders"] is not None,
    ),
    Format("{error_message}", when="error_message"),
    # если заказов больше 5 выводим меню с пагинацией
    ScrollingGroup(
        Select(
            Format("📦 Заказ №{item[user_order_id]} от {item[created_at_moscow]}"),
            id="order_button",
            item_id_getter=lambda x: x["id"],
            items="orders",
            on_click=history_order_button,
        ),
        id="orders_scroll",
        width=1,
        height=5,
        when=lambda data, *_: data["orders"] and len(data["orders"]) > 5,
    ),
    # если заказов меньше либо равно 5 выводим обычный список кнопок
    Group(
        Select(
            Format("📦 Заказ №{item[user_order_id]} от {item[created_at_moscow]}"),
            id="order_button",
            item_id_getter=lambda x: x["id"],
            items="orders",
            on_click=history_order_button,
        ),
        width=1,
        when=lambda data, *_: data["orders"] and len(data["orders"]) <= 5,
    ),
    Cancel(
        text=Const("🔙 Назад в Профиль!"),
        id="__profile__",
    ),
    getter=history_orders_getter,
    state=HistoryOrdersSG.orders,
)


# Окно отображения информации о выполненном заказе
history_order_detail_window = Window(
    Format("{error_message}", when="error_message"),
    Format("📦 Заказ №{user_order_id}"),
    Format("📅 Дата: {created_at_moscow}\n"),
    Format("📜 Состав заказа:"),
    List(
        Format(
            "- {item[name]} {item[size_name]} x {item[quantity]} шт. |  {item[total_price]} руб."
        ),
        items="order_items",
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
        text=Const("🔄 Повторить заказ"),
        id="repeat_order",
        on_click=repeat_order,
    ),
    SwitchTo(
        text=Const("🔙 Назад"),
        id="back_to_history_orders",
        state=HistoryOrdersSG.orders,
    ),
    Cancel(
        text=Const("🔙 Назад в Профиль!"),
        id="__profile__",
    ),
    getter=history_order_detail_getter,
    state=HistoryOrdersSG.order_detail,
)


dialog = Dialog(history_orders_window, history_order_detail_window)
