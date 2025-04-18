from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, Dialog, Window
from aiogram_dialog.widgets.text import Const, Format, Case, Multi
from aiogram_dialog.widgets.kbd import (
    Button,
    Select,
    Cancel,
    ScrollingGroup,
    Group,
    Start,
)
from aiogram_dialog.widgets.media import StaticMedia
from dialogs.states import CartsSG, CheckoutOrderSG
from services.api_client import APIClient, APIError
from db.operations import UserDO
from config import settings


# Хэндлер кнопки удаления корзины
async def clear_cart(
    callback: CallbackQuery, widget: Button, dialog_manager: DialogManager
):
    tg_id = str(dialog_manager.event.from_user.id)
    session = dialog_manager.middleware_data["session"]
    user = await UserDO.get_by_tg_id(tg_id=tg_id, session=session)
    try:
        async with APIClient(user.email) as api:
            await api.delete("/carts/")
            dialog_manager.dialog_data.clear()
            await dialog_manager.update({})
            await callback.answer("Корзина очищена 🧹")
    except APIError:
        error_message = "Произошла ошибка при очистке корзины."
        await callback.answer(f"⚠️ Ошибка: {error_message}")


# Хэндлер обработки нажатия кнопки продукта из корзины
async def cart_item_button(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
):
    product_id, size_id = map(int, item_id.split("_"))
    dialog_manager.dialog_data["product_id"] = product_id
    dialog_manager.dialog_data["size_id"] = size_id
    if "cart_item_data" not in dialog_manager.dialog_data:
        tg_id = str(dialog_manager.event.from_user.id)
        session = dialog_manager.middleware_data["session"]
        user = await UserDO.get_by_tg_id(tg_id=tg_id, session=session)
        try:
            async with APIClient(user.email) as api:
                cart_item = await api.get(f"/carts/{product_id}/{size_id}/")
                dialog_manager.dialog_data.update(
                    {
                        "cart_item_data": cart_item,
                        "quantity": cart_item["quantity"],
                        "total_price": float(cart_item["total_price"]),
                        "price_product": float(
                            cart_item["product"]["final_price"]
                        ),
                    }
                )
                await dialog_manager.switch_to(state=CartsSG.cart_item)
        except APIError:
            await callback.answer(
                "⚠️ Не удалось загрузить информацию о продукте."
            )


# Хэндлер кнопки увелечения количества продукта
async def increase_quantity(
    callback: CallbackQuery, widget: Button, dialog_manager: DialogManager
):
    current_quantity = dialog_manager.dialog_data.get("quantity")
    price_product = dialog_manager.dialog_data.get("price_product")
    dialog_manager.dialog_data.update(
        {
            "quantity": current_quantity + 1,
            "total_price": price_product * (current_quantity + 1),
        }
    )
    await dialog_manager.update({})


# Хэндлер кнопки уменьшения продукта
async def decrease_quantity(
    callback: CallbackQuery, widget: Button, dialog_manager: DialogManager
):
    current_quantity = dialog_manager.dialog_data.get("quantity")
    price_product = dialog_manager.dialog_data.get("price_product")
    # уменьшаем количество но не меньше 1
    new_quantity = max(1, current_quantity - 1)
    dialog_manager.dialog_data.update(
        {
            "quantity": new_quantity,
            "total_price": price_product * new_quantity,
        }
    )
    await dialog_manager.update({})


# Хэндлер кнопки обновления количества
async def update_quantity(
    callback: CallbackQuery, widget: Button, dialog_manager: DialogManager
):
    product_id = int(dialog_manager.dialog_data["product_id"])
    size_id = int(dialog_manager.dialog_data["size_id"])
    tg_id = str(dialog_manager.event.from_user.id)
    session = dialog_manager.middleware_data["session"]
    user = await UserDO.get_by_tg_id(tg_id=tg_id, session=session)
    quantity = dialog_manager.dialog_data.get("quantity")
    data = {"quantity": quantity}
    try:
        async with APIClient(user.email) as api:
            await api.patch(
                f"/carts/update/{product_id}/{size_id}/",
                data=data,
            )
            cart_item = await api.get(f"/carts/{product_id}/{size_id}/")
            dialog_manager.dialog_data["cart_item_data"] = cart_item
            await callback.answer("Количество продукта обновлено")
            await dialog_manager.update({})
    except APIError:
        error_message = "Не удалось обновить количество."
        await callback.answer(f"⚠️ Ошибка: {error_message}")


# Хэндлер кнопки удаления продукта из корзины
async def delete_cart_item(
    callback: CallbackQuery, widget: Button, dialog_manager: DialogManager
):
    product_id = int(dialog_manager.dialog_data["product_id"])
    size_id = int(dialog_manager.dialog_data["size_id"])
    tg_id = str(dialog_manager.event.from_user.id)
    session = dialog_manager.middleware_data["session"]
    user = await UserDO.get_by_tg_id(tg_id=tg_id, session=session)
    try:
        async with APIClient(user.email) as api:
            await api.delete(f"/carts/delete/{product_id}/{size_id}/")
            if "cart_item_data" in dialog_manager.dialog_data:
                del dialog_manager.dialog_data["cart_item_data"]
            if "quantity" in dialog_manager.dialog_data:
                del dialog_manager.dialog_data["quantity"]
            if "total_price" in dialog_manager.dialog_data:
                del dialog_manager.dialog_data["total_price"]
            await dialog_manager.switch_to(state=CartsSG.carts)
            await callback.answer("Продукт удален из корзины 🗑️")
    except APIError:
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
    try:
        async with APIClient(user.email) as api:
            carts = await api.get("/carts/")
            return {
                "total_amount": carts["total_amount"],
                "cart_items": carts["cart_items"],
            }
    except APIError:
        cart_items = None
    error_message = (
        "Не удалось загрузить данные корзины."
        if not cart_items
        else None
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
    photo_url = None
    if cart_item_data["product"]['photo_path']:
        photo_url = (
            f"{settings.S3_HOST}"
            f"{settings.S3_BACKET}"
            f"{cart_item_data['product']['photo_path']}"
        )
    return {
        "name": cart_item_data["product"]["name"],
        "size_name": cart_item_data["product"]["size_name"],
        "total_price": f"{total_price:.2f}",
        "quantity": quantity,
        "photo_url": photo_url,
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
            Format(
                "{item[product][name]} "
                "{item[product][size_name]} x "
                "{item[quantity]}"
            ),
            id="cart_button",
            item_id_getter=lambda x: (
                f"{x['product']['id']}_"
                f"{x['product']['size_id']}"
            ),
            items="cart_items",
            on_click=cart_item_button,
        ),
        id="carts_scroll",
        width=1,
        height=5,
        when=lambda data, *_: (
            data["cart_items"] and
            len(data["cart_items"]) > 5
        ),
    ),
    # если продуктов в корзине меньше или равно 5, выводим меню с списком
    Group(
        Select(
            Format(
                "{item[product][name]} "
                "{item[product][size_name]} x "
                "{item[quantity]}"
            ),
            id="cart_button",
            item_id_getter=lambda x: (
                f"{x['product']['id']}_"
                f"{x['product']['size_id']}"
            ),
            items="cart_items",
            on_click=cart_item_button,
        ),
        width=1,
        when=lambda data, *_: (
            data["cart_items"] and
            len(data["cart_items"]) <= 5
        ),
    ),
    # кнопки Очистить корзину и Перейти к оформлению заказа
    # выводятся только если есть элементы в корзине
    Button(
        Const("🗑️ Очистить корзину"),
        id="clear_cart",
        on_click=clear_cart,
        when="cart_items",
    ),
    Start(
        Const("🚀 Перейти к оформлению заказа"),
        id="checkout",
        state=CheckoutOrderSG.select_delivery_type,
        when="cart_items",
    ),
    Cancel(
        text=Const("🔙 Назад в Меню!"),
        id="__menu__",
    ),
    getter=carts_getter,
    state=CartsSG.carts,
)


# Окно отображения продукта в корзине
cart_item_window = Window(
    StaticMedia(url=Format("{photo_url}"), when="photo_url"),
    Format("🏷️ Наименование: {name} "),
    Format("📏 Размер: {size_name}"),
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
    Cancel(
        text=Const("🔙 Назад в Меню!"),
        id="__menu__",
    ),
    getter=cart_item_getter,
    state=CartsSG.cart_item,
)


dialog = Dialog(carts_window, cart_item_window)
