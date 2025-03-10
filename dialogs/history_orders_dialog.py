from datetime import datetime
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, Dialog, Window
from aiogram_dialog.widgets.text import Const, Format, Case, List
from aiogram_dialog.widgets.kbd import (
    SwitchTo,
    Select,
    Cancel,
    ScrollingGroup,
    Group,
)
from dialogs.states import OrdersSG
from services.api_client import APIClient
from db.operations import UserDO


# Функция для форматирования даты в читаемы формат
def formatted_date(utc_date: str):
    dt = datetime.strptime(utc_date, "%Y-%m-%dT%H:%M:%S.%f")
    formatted_date = dt.strftime("%d.%m.%Y")
    return formatted_date


# Хэндлер обработки нажотой кнопки заказа
async def order_button(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: int,
):
    dialog_manager.dialog_data["order_id"] = item_id
    await dialog_manager.switch_to(state=OrdersSG.order_detail)


# Геттер для получения списка заказов и передачи в окно
async def history_orders_getter(dialog_manager: DialogManager, **kwargs):
    tg_id = str(dialog_manager.event.from_user.id)
    session = dialog_manager.middleware_data["session"]
    user = await UserDO.get_by_tg_id(tg_id=tg_id, session=session)
    async with APIClient(user.email) as api:
        response = await api.get("/orders/")
        if response["success"]:
            orders = response["data"]
            for order in orders:
                created_at = order.get("created_at")
                order["created_at"] = formatted_date(created_at)
        else:
            orders = None
        error_message = "История заказов временно недоступна." if not orders else None
        return {"orders": orders, "error_message": error_message}


# Геттер для получения заказа по id и передачи в окно
async def order_detail_getter(dialog_manager: DialogManager, **kwargs):
    order_id = dialog_manager.dialog_data["order_id"]
    tg_id = str(dialog_manager.event.from_user.id)
    session = dialog_manager.middleware_data["session"]
    user = await UserDO.get_by_tg_id(tg_id=tg_id, session=session)
    async with APIClient(user.email) as api:
        response = await api.get(f"/orders/{order_id}/")
        if response["success"]:
            order = response["data"]
            return {
                "id": order["id"],
                "order_items": order["order_items"],
                "created_at": formatted_date(order["created_at"]),
                "total_amount": order["total_amount"],
            }
        else:
            return {
                "id": "Информация о заказе временно недоступна",
                "order_items": [],
                "created_at": "-",
                "total_amount": 0,
            }


# Окно отображения всех заказаов пользователя
history_orders_window = Window(
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
            on_click=order_button,
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
            on_click=order_button,
        ),
        width=1,
        when=lambda data, *_: data["orders"] and len(data["orders"]) <= 5,
    ),
    Cancel(text=Const("🔙 Назад в Меню!"), id="__main__"),
    getter=history_orders_getter,
    state=OrdersSG.orders,
)


# Окно отображения информации о заказе
order_detail_window = Window(
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
        state=OrdersSG.orders,
    ),
    Cancel(text=Const("🔙 Назад в Меню!"), id="__main__"),
    getter=order_detail_getter,
    state=OrdersSG.order_detail,
)


dialog = Dialog(history_orders_window, order_detail_window)
