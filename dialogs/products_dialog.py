from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, Dialog, Window
from aiogram_dialog.widgets.text import Const, Format, Multi
from aiogram_dialog.widgets.kbd import (
    Button,
    SwitchTo,
    Select,
    Cancel,
    ScrollingGroup,
    Group,
)
from aiogram_dialog.widgets.media import StaticMedia
from dialogs.states import ProductsSG
from services.api_client import APIClient, APIError
from db.operations import UserDO
from config import settings


# Хэндлер обработки выбранной категории
async def category_button(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
):
    categories = dialog_manager.dialog_data["categories"]
    category_name = "Продукты"
    for category in categories:
        if category["id"] == int(item_id):
            category_name = category["name"]
            break
    dialog_manager.dialog_data.update(
        {"category_id": item_id, "category_name": category_name}
    )
    await dialog_manager.switch_to(state=ProductsSG.products)


# Хэндлер обработки выбранного продукта
async def product_button(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
):
    """Обработчик выбора продукта"""
    try:
        async with APIClient() as api:
            product_detail = await api.get(f"/products/{item_id}/")

        sizes = [
            {
                "id": size_data["size"]["id"],
                "name": size_data["size"]["name"],
                "final_price": size_data["final_price"],
            }
            for size_data in product_detail["product_sizes"]
        ]
        default_size = sizes[0] if sizes else None
        photo_url = None
        if product_detail['photo_path']:
            photo_url = (
                f"{settings.S3_HOST}"
                f"{settings.S3_BACKET}"
                f"{product_detail['photo_path']}"
            )
        dialog_manager.dialog_data.update(
            {
                "product_id": item_id,
                "product_name": product_detail["name"],
                "description": product_detail.get("description"),
                "photo_url": photo_url,
                "sizes": sizes,
                "selected_size_id": (
                    default_size["id"] if default_size else None
                ),
                "selected_price": (
                    default_size["final_price"] if default_size else "—"
                ),
                "selected_size_name": (
                    default_size["name"] if default_size else "Не выбран"
                ),
            }
        )
        await dialog_manager.switch_to(state=ProductsSG.product_detail)

    except APIError:
        await callback.answer("⚠️ Ошибка: Не удалось загрузить продукт.")


# Хэндлер выбора размера
async def size_button(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
):
    sizes = dialog_manager.dialog_data.get("sizes", [])
    selected_size = None
    for size in sizes:
        if size["id"] == int(item_id):
            selected_size = size
            break
    if selected_size:
        dialog_manager.dialog_data.update(
            {
                "selected_size_id": selected_size["id"],
                "selected_price": selected_size["final_price"],
                "selected_size_name": selected_size["name"],
            }
        )
        await callback.answer(f"Выбран размер: {selected_size['name']}")
        await dialog_manager.update({})

    else:
        await callback.answer("⚠️ Ошибка: Размер не найден.")


# Хэндлер добавления продукта в корзину
async def add_to_cart_button(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager,
):
    tg_id = str(callback.from_user.id)
    session = dialog_manager.middleware_data["session"]
    user = await UserDO.get_by_tg_id(tg_id=tg_id, session=session)
    product_id = dialog_manager.dialog_data["product_id"]
    product_name = dialog_manager.dialog_data["product_name"]
    size_id = dialog_manager.dialog_data["selected_size_id"]
    size_name = dialog_manager.dialog_data["selected_size_name"]
    try:
        async with APIClient(user.email) as api:
            await api.post(f"/carts/add/{product_id}/{size_id}/")
            await callback.answer(
                f"{product_name} {size_name} добавлен(а) в корзину ✅"
            )
    except APIError:
        error_message = "Произошла неизвестная ошибка."
        await callback.answer(f"⚠️ Ошибка: {error_message}")


# Геттер для получения всех категорий и передаче в окно
async def categories_getter(dialog_manager: DialogManager, **kwargs):
    try:
        async with APIClient() as api:
            categories = await api.get("/category/")
    except APIError:
        categories = []
    dialog_manager.dialog_data["categories"] = categories
    error_message = (
        "Категории временно недоступны."
        if not categories
        else None
    )
    return {"categories": categories, "error_message": error_message}


# Геттер для получения всех продуктов этой категории и передаче в окно
async def products_getter(dialog_manager: DialogManager, **kwargs):
    category_id = dialog_manager.dialog_data["category_id"]
    category_name = dialog_manager.dialog_data["category_name"]
    try:
        async with APIClient() as api:
            products = await api.get(f"/products/?category_id={category_id}")
    except APIError:
        products = None
    error_message = "Продукты временно недоступны." if not products else None
    return {
        "products": products,
        "category_name": category_name,
        "error_message": error_message,
    }


# Гетер для получения информации о продукте и передаче в окно
async def product_detail_getter(dialog_manager: DialogManager, **kwargs):
    return {
        "name": dialog_manager.dialog_data.get("product_name"),
        "description": dialog_manager.dialog_data.get("description"),
        "photo_url": dialog_manager.dialog_data.get("photo_url"),
        "sizes": dialog_manager.dialog_data.get("sizes", []),
        "selected_size_name": dialog_manager.dialog_data.get(
            "selected_size_name", "Не выбран"
        ),
        "selected_price": (
            dialog_manager.dialog_data.get("selected_price", "—")
        ),
    }


# Окно отображения категорий
categories_window = Window(
    Multi(
        Const("📂 Категории"),
        Format("{error_message}", when="error_message"),
    ),
    ScrollingGroup(
        Select(
            Format("📁 {item[name]}"),
            id="categories_button",
            item_id_getter=lambda x: f"{x["id"]}_{x["name"]}",
            items="categories",
            on_click=category_button,
        ),
        id="categories_scroll_menu",
        width=1,
        height=5,
        when=lambda data, *_: (
            data["categories"] and
            len(data["categories"]) > 5
        ),
    ),
    Group(
        Select(
            Format("{item[name]}"),
            id="categories_button",
            item_id_getter=lambda x: x["id"],
            items="categories",
            on_click=category_button,
        ),
        id="categories_list_menu",
        width=1,
        when=lambda data, *_: (
            data["categories"] and
            len(data["categories"]) <= 5
        ),
    ),
    Cancel(
        text=Const("🔙 Назад в Меню!"),
        id="__menu__",
    ),
    getter=categories_getter,
    state=ProductsSG.categories,
)

# Окно отображения продуктов
products_window = Window(
    Multi(
        Format("{category_name}"),
        Format("{error_message}", when="error_message"),
    ),
    ScrollingGroup(
        Select(
            Format("{item[name]}"),
            id="products_button",
            item_id_getter=lambda x: x["id"],
            items="products",
            on_click=product_button,
        ),
        id="scroll_list_menu",
        width=1,
        height=5,
        when=lambda data, *_: (
            data["products"] and
            len(data["products"]) > 5
        ),
    ),
    Group(
        Select(
            Format("{item[name]}"),
            id="products_button",
            item_id_getter=lambda x: x["id"],
            items="products",
            on_click=product_button,
        ),
        id="products_list_menu",
        width=1,
        when=lambda data, *_: (
            data["products"] and
            len(data["products"]) <= 5
        ),
    ),
    SwitchTo(
        text=Const("🔙 Назад"),
        id="back_to_category",
        state=ProductsSG.categories,
    ),
    Cancel(
        text=Const("🔙 Назад в Меню!"),
        id="__menu__",
    ),
    getter=products_getter,
    state=ProductsSG.products,
)

# Окно отображения информации о продукте
product_detail_window = Window(
    StaticMedia(url=Format("{photo_url}"), when="photo_url"),
    Format("🏷️ Наименование: {name}"),
    Format("📝 Описание: {description}", when="description"),
    Format("📏 Размер: {selected_size_name}"),
    Format("💰 Цена: {selected_price} руб."),
    Select(
        Format("{item[name]}"),
        id="size_button",
        item_id_getter=lambda x: x["id"],
        items="sizes",
        on_click=size_button,
    ),
    Button(
        text=Const("🛒 Добавить в корзину"),
        id="add_to_cart",
        on_click=add_to_cart_button,
        when="sizes",
    ),
    SwitchTo(
        text=Const("🔙 Назад"),
        id="back_to_products",
        state=ProductsSG.products,
    ),
    Cancel(
        text=Const("🔙 Назад в Меню!"),
        id="__menu__",
    ),
    getter=product_detail_getter,
    state=ProductsSG.product_detail,
)


dialog = Dialog(categories_window, products_window, product_detail_window)
