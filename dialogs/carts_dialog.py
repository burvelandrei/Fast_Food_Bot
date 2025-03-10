from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, Dialog, Window
from aiogram_dialog.widgets.text import Const, Format, Case, Multi
from aiogram_dialog.widgets.kbd import (
    Button,
    Select,
    Cancel,
    ScrollingGroup,
    Group,
)
from aiogram_dialog.widgets.media import StaticMedia
from environs import Env
from dialogs.states import CartsSG
from services.api_client import APIClient
from db.operations import UserDO


env = Env()
env.read_env()


# Хэндлер кнопки удаления корзины
async def clear_cart(
    callback: CallbackQuery, widget: Button, dialog_manager: DialogManager
):
    tg_id = str(dialog_manager.event.from_user.id)
    session = dialog_manager.middleware_data["session"]
    user = await UserDO.get_by_tg_id(tg_id=tg_id, session=session)
    async with APIClient(user.email) as api:
        response = await api.delete("/carts/")
        if response["success"]:
            dialog_manager.dialog_data.clear()
            await dialog_manager.update({})
            await callback.answer("Корзина очищена 🧹")
        else:
            error_message = "Произошла ошибка при очистке корзины."
            await callback.answer(f"⚠️ Ошибка: {error_message}")


# Хэндлер кнопки оформления заказа
async def confirmation_order(
    callback: CallbackQuery, widget: Button, dialog_manager: DialogManager
):
    tg_id = str(dialog_manager.event.from_user.id)
    session = dialog_manager.middleware_data["session"]
    user = await UserDO.get_by_tg_id(tg_id=tg_id, session=session)
    async with APIClient(user.email) as api:
        response = await api.post("/orders/confirmation/")
        if response["success"]:
            await callback.answer("Заказ успешно оформлен 🎉")
        else:
            error_message = "Не удалось оформить заказ."
            await callback.answer(f"⚠️ Ошибка: {error_message}")


# Хэндлер обработки нажатия кнопки продукта из корзины
async def cart_item_button(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: int,
):
    dialog_manager.dialog_data["product_id"] = item_id
    if "cart_item_data" not in dialog_manager.dialog_data:
        tg_id = str(dialog_manager.event.from_user.id)
        session = dialog_manager.middleware_data["session"]
        user = await UserDO.get_by_tg_id(tg_id=tg_id, session=session)
        async with APIClient(user.email) as api:
            response = await api.get(f"/carts/{item_id}/")

            if response["success"]:
                dialog_manager.dialog_data["cart_item_data"] = response["data"]
                dialog_manager.dialog_data["quantity"] = response["data"]["quantity"]
                dialog_manager.dialog_data["total_price"] = float(
                    response["data"]["total_price"]
                )
                dialog_manager.dialog_data["price_product"] = float(
                    response["data"]["product"]["final_price"]
                )
            else:
                await callback.answer("⚠️ Не удалось загрузить информацию о продукте.")
                return

    await dialog_manager.switch_to(state=CartsSG.cart_item)


# Хэндлер кнопки увелечения количества продукта
async def increase_quantity(
    callback: CallbackQuery, widget: Button, dialog_manager: DialogManager
):
    current_quantity = dialog_manager.dialog_data.get("quantity")
    price_product = dialog_manager.dialog_data.get("price_product")
    dialog_manager.dialog_data["quantity"] = current_quantity + 1
    dialog_manager.dialog_data["total_price"] = price_product * (current_quantity + 1)
    await dialog_manager.update({})


# Хэндлер кнопки уменьшения продукта
async def decrease_quantity(
    callback: CallbackQuery, widget: Button, dialog_manager: DialogManager
):
    current_quantity = dialog_manager.dialog_data.get("quantity")
    price_product = dialog_manager.dialog_data.get("price_product")
    # уменьшаем количество но не меньше 1
    new_quantity = max(1, current_quantity - 1)
    dialog_manager.dialog_data["quantity"] = new_quantity
    dialog_manager.dialog_data["total_price"] = price_product * new_quantity
    await dialog_manager.update({})


# Хэндлер кнопки обновления количества
async def update_quantity(
    callback: CallbackQuery, widget: Button, dialog_manager: DialogManager
):
    product_id = int(dialog_manager.dialog_data["product_id"])
    tg_id = str(dialog_manager.event.from_user.id)
    session = dialog_manager.middleware_data["session"]
    user = await UserDO.get_by_tg_id(tg_id=tg_id, session=session)
    quantity = dialog_manager.dialog_data.get("quantity")
    data = {"product_id": product_id, "quantity": quantity}
    async with APIClient(user.email) as api:
        response = await api.post("/carts/update/", data=data)
        if response["success"]:
            response = await api.get(f"/carts/{product_id}/")
            dialog_manager.dialog_data["cart_item_data"] = response["data"]
            await callback.answer("Количество продукта обновлено")
            await dialog_manager.update({})
        else:
            error_message = "Не удалось обновить количество."
            await callback.answer(f"⚠️ Ошибка: {error_message}")


# Хэндлер кнопки удаления продукта из корзины
async def delete_cart_item(
    callback: CallbackQuery, widget: Button, dialog_manager: DialogManager
):
    product_id = int(dialog_manager.dialog_data["product_id"])
    tg_id = str(dialog_manager.event.from_user.id)
    session = dialog_manager.middleware_data["session"]
    user = await UserDO.get_by_tg_id(tg_id=tg_id, session=session)
    async with APIClient(user.email) as api:
        response = await api.delete(f"/carts/{product_id}/")
        if response["success"]:
            if "cart_item_data" in dialog_manager.dialog_data:
                del dialog_manager.dialog_data["cart_item_data"]
            if "quantity" in dialog_manager.dialog_data:
                del dialog_manager.dialog_data["quantity"]
            if "total_price" in dialog_manager.dialog_data:
                del dialog_manager.dialog_data["total_price"]
            await dialog_manager.switch_to(state=CartsSG.carts)
            await callback.answer("Продукт удален из корзины 🗑️")
        else:
            error_message = "Не удалось удалить продукт."
            await callback.answer(f"⚠️ Ошибка: {error_message}")


# Хэндлер кнопки назад в корзину
async def back_to_cart(
    callback: CallbackQuery, widget: Button, dialog_manager: DialogManager
):
    # Очищаем кэш
    if "cart_item_data" in dialog_manager.dialog_data:
        del dialog_manager.dialog_data["cart_item_data"]
    if "quantity" in dialog_manager.dialog_data:
        del dialog_manager.dialog_data["quantity"]
    if "total_price" in dialog_manager.dialog_data:
        del dialog_manager.dialog_data["total_price"]
    await dialog_manager.switch_to(state=CartsSG.carts)


# Гетер получения данных корзины и передачи в окно
async def carts_getter(dialog_manager: DialogManager, **kwargs):
    tg_id = str(dialog_manager.event.from_user.id)
    session = dialog_manager.middleware_data["session"]
    user = await UserDO.get_by_tg_id(tg_id=tg_id, session=session)
    async with APIClient(user.email) as api:
        response = await api.get("/carts/")
        if response["success"]:
            carts = response["data"]
            return {
                "total_amount": carts["total_amount"],
                "cart_items": carts["cart_items"],
            }
        else:
            cart_items = None
            error_message = (
                "Не удалось загрузить данные корзины." if not cart_items else None
            )
            return {
                "total_amount": 0,
                "cart_items": cart_items,
                "error_message": error_message,
            }


# Гетер получения данных продукта из корзины и передачи в окно
async def cart_item_getter(dialog_manager: DialogManager, **kwargs):
    cart_item_data = dialog_manager.dialog_data.get("cart_item_data")
    quantity = dialog_manager.dialog_data.get("quantity")
    total_price = dialog_manager.dialog_data.get("total_price")
    check_image = cart_item_data["product"]["photo_url"]
    photo_s3_url = None
    if check_image:
        photo_s3_url = f"{env('S3_HOST')}{env('S3_BACKET')}{cart_item_data['product']['photo_url']}"
    return {
        "name": cart_item_data["product"]["name"],
        "total_price": f"{total_price:.2f}",
        "quantity": quantity,
        "photo_s3_url": photo_s3_url,
        "check_image": check_image,
    }


# Окно корзины
carts_window = Window(
    # если продуктов корзине нет, выводим то что нет продуктов
    Case(
        {
            "True": Format("Пока тут пусто 😔"),
            "False": Multi(
                Format("🛒 Ваша корзина:"),
                Format("💰 Общая сумма корзины: {total_amount} руб."),
                Format("👇 Выберите продукт для изменения количества:"),
            ),
        },
        selector=lambda data, *_: str(not bool(data["cart_items"])),
        when=lambda data, *_: data["cart_items"] is not None,
    ),
    Format("{error_message}", when="error_message"),
    # если продуктов в корзине больше 5, выводим меню с пагинацией
    ScrollingGroup(
        Select(
            Format("{item[product][name]} - {item[quantity]}"),
            id="cart_button",
            item_id_getter=lambda x: x["product"]["id"],
            items="cart_items",
            on_click=cart_item_button,
        ),
        id="carts_scroll",
        width=1,
        height=5,
        when=lambda data, *_: data["cart_items"] and len(data["cart_items"]) > 5,
    ),
    # если продуктов в корзине меньше или равно 5, выводим меню с списком
    Group(
        Select(
            Format("{item[product][name]} х {item[quantity]}шт."),
            id="cart_button",
            item_id_getter=lambda x: x["product"]["id"],
            items="cart_items",
            on_click=cart_item_button,
        ),
        width=1,
        when=lambda data, *_: data["cart_items"] and len(data["cart_items"]) <= 5,
    ),
    # кнопки Очистить корзину и Оформить заказ выводятся только если есть элементы в корзине
    Button(
        Const("🗑️ Очистить корзину"),
        id="clear_cart",
        on_click=clear_cart,
        when="cart_items",
    ),
    Button(
        Const("🚀 Оформить заказ"),
        id="checkout",
        on_click=confirmation_order,
        when="cart_items",
    ),
    Cancel(
        text=Const("🔙 Назад в Меню!"),
        id="__main__",
    ),
    getter=carts_getter,
    state=CartsSG.carts,
)


cart_item_window = Window(
    StaticMedia(url=Format("{photo_s3_url}"), when="check_image"),
    Format("🏷️ Наименование: {name}"),
    Format("💰 Общая цена: {total_price} руб."),
    Group(
        Button(
            Const("➖"),
            id="decrease_quantity",
            on_click=decrease_quantity,
        ),
        Button(Format("{quantity}"), id="current_quantity"),
        Button(
            Const("➕"),
            id="increase_quantity",
            on_click=increase_quantity,
        ),
        width=3,
    ),
    Button(
        Const("🔄 Обновить"),
        id="update_quantity",
        on_click=update_quantity,
    ),
    Button(
        Const("🗑️ Удалить из корзины"),
        id="delete_cart_item",
        on_click=delete_cart_item,
    ),
    Button(
        Const("🔙 Назад"),
        id="back_to_cart",
        on_click=back_to_cart,
    ),
    Cancel(text=Const("🔙 Назад в Меню!"), id="__main__"),
    getter=cart_item_getter,
    state=CartsSG.cart_item,
)


dialog = Dialog(carts_window, cart_item_window)
