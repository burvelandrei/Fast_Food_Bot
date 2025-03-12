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
from dialogs.states import CurrentOrdersSG
from services.api_client import APIClient, APIError
from db.operations import UserDO


# Функция для форматирования даты и времени в читаемый формат (с переводом в МСК)
def formatted_date(utc_date: str):
    dt = datetime.strptime(utc_date, "%Y-%m-%dT%H:%M:%S.%f")
    dt_msk = dt + timedelta(hours=3)
    formatted_date = dt_msk.strftime("%d.%m.%Y %H:%M")
    return formatted_date


# Хэндлер обработки нажотой кнопки выполненного заказа
async def current_order_button(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: int,
):
    dialog_manager.dialog_data["order_id"] = item_id
    await dialog_manager.switch_to(state=CurrentOrdersSG.order_detail)


# Геттер для получения списка истории заказов и передачи в окно
async def current_orders_getter(dialog_manager: DialogManager, **kwargs):
    tg_id = str(dialog_manager.event.from_user.id)
    session = dialog_manager.middleware_data["session"]
    user = await UserDO.get_by_tg_id(tg_id=tg_id, session=session)
    try:
        async with APIClient(user.email) as api:
            orders = await api.get("/orders/?status=processing")
            for order in orders:
                created_at = order.get("created_at")
                order["created_at"] = formatted_date(created_at)
    except APIError:
        orders = None
    error_message = "История заказов временно недоступна." if orders is None else None
    return {"orders": orders, "error_message": error_message}


# Геттер для получения выполненного заказа по id и передачи в окно
async def current_order_detail_getter(dialog_manager: DialogManager, **kwargs):
    order_id = dialog_manager.dialog_data["order_id"]
    tg_id = str(dialog_manager.event.from_user.id)
    session = dialog_manager.middleware_data["session"]
    user = await UserDO.get_by_tg_id(tg_id=tg_id, session=session)
    try:
        async with APIClient(user.email) as api:
            order = await api.get(f"/orders/{order_id}/")
            return {
                "id": order["id"],
                "order_items": order["order_items"],
                "created_at": formatted_date(order["created_at"]),
                "total_amount": order["total_amount"],
                "error_message": None,
            }
    except APIError:
        return {
            "id": "-",
            "order_items": [],
            "created_at": "-",
            "total_amount": 0,
            "error_message": "Информация о заказе временно недоступна",
        }


# Окно отображения истории заказаов пользователя
current_orders_window = Window(
    # если заказов выводим то что нет заказов
    Case(
        {
            "True": Format("У вас пока нет заказов 😔"),
            "False": Format("📋 Выберите заказ для просмотра:"),
        },
        selector=lambda data, *_: str(not bool(data["orders"])),
        when=lambda data, *_: data["orders"] is not None,
    ),
    Format("{error_message}", when="error_message"),
    # если заказов больше 5 выводим меню с пагинацией
    ScrollingGroup(
        Select(
            Format("📦 Заказ №{item[id]} от {item[created_at]}"),
            id="order_button",
            item_id_getter=lambda x: x["id"],
            items="orders",
            on_click=current_order_button,
        ),
        id="orders_scroll",
        width=1,
        height=5,
        when=lambda data, *_: data["orders"] and len(data["orders"]) > 5,
    ),
    # если заказов меньше либо равно 5 выводим обычный список кнопок
    Group(
        Select(
            Format("📦 Заказ №{item[id]} от {item[created_at]}"),
            id="order_button",
            item_id_getter=lambda x: x["id"],
            items="orders",
            on_click=current_order_button,
        ),
        width=1,
        when=lambda data, *_: data["orders"] and len(data["orders"]) <= 5,
    ),
    Cancel(text=Const("🔙 Назад в Профиль!"), id="__main__"),
    getter=current_orders_getter,
    state=CurrentOrdersSG.orders,
)


# Окно отображения информации о выполненном заказе
current_order_detail_window = Window(
    Format("{error_message}", when="error_message"),
    Format("📦 Заказ №{id}"),
    Format("📅 Дата: {created_at}\n"),
    Format("📜 Состав заказа:"),
    List(
        Format("- {item[name]} x {item[quantity]} шт. |  {item[total_price]} руб."),
        items="order_items",
    ),
    Format("\n💰  Итоговая сумма: {total_amount} руб."),
    SwitchTo(
        text=Const("🔙 Назад"),
        id="back_to_history_orders",
        state=CurrentOrdersSG.orders,
    ),
    Cancel(text=Const("🔙 Назад в Профиль!"), id="__main__"),
    getter=current_order_detail_getter,
    state=CurrentOrdersSG.order_detail,
)


dialog = Dialog(current_orders_window, current_order_detail_window)
