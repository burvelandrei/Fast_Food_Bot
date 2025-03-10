from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import (
    Button,
    SwitchTo,
    Select,
    Cancel,
    ScrollingGroup,
    Group,
)
from aiogram_dialog.widgets.media import StaticMedia
from environs import Env
from dialogs.states import ProductsSG
from services.api_client import APIClient
from db.operations import UserDO


env = Env()
env.read_env()


# Хэндлер обработки выбранной категории
async def category_button(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: int,
):
    dialog_manager.dialog_data["category_id"] = item_id
    await dialog_manager.switch_to(state=ProductsSG.products)


# Хэндлер обработки выбранного продукта
async def product_button(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: int,
):
    dialog_manager.dialog_data["product_id"] = item_id
    await dialog_manager.switch_to(state=ProductsSG.product_detail)


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
    data = {
        "product_id": product_id,
        "quantity": 1,
    }

    async with APIClient(user.email) as api:
        response = await api.post("/carts/add/", data=data)

    if response["success"]:
        await callback.answer(f"{product_name} добавлен(а) в корзину ✅")
    else:
        error_message = "Произошла неизвестная ошибка."
        await callback.answer(f"⚠️ Ошибка: {error_message}")


# Геттер для получения всех категорий и передаче в окно
async def categories_getter(dialog_manager: DialogManager, **kwargs):
    async with APIClient() as api:
        response = await api.get("/category/")
    if response["success"]:
        categories = response["data"]
    else:
        categories = None
    error_message = "Категории временно недоступны." if not categories else None
    return {"categories": categories, "error_message": error_message}


# Геттер для получения всех продуктов этой категории и передаче в окно
async def products_getter(dialog_manager: DialogManager, **kwargs):
    category_id = dialog_manager.dialog_data["category_id"]
    async with APIClient() as api:
        response = await api.get(f"/products/?category_id={category_id}")
    if response["success"]:
        products = response["data"]
    else:
        products = None
    error_message = "Продукты временно недоступны." if not products else None
    return {"products": products, "error_message": error_message}


# Гетер для получения информации о продукте и передаче в окно
async def product_detail_getter(dialog_manager: DialogManager, **kwargs):
    product_id = dialog_manager.dialog_data.get("product_id")

    async with APIClient() as api:
        response = await api.get(f"/products/{product_id}/")

    if response["success"]:
        product_detail = response["data"]
        dialog_manager.dialog_data["product_name"] = product_detail["name"]
        check_image = product_detail.get("photo_url")
        photo_s3_url = None
        if check_image:
            photo_s3_url = (
                f"{env('S3_HOST')}{env('S3_BACKET')}{product_detail['photo_url']}"
            )
        return {
            "name": product_detail["name"],
            "description": product_detail.get("description", "Описание не доступно."),
            "price": product_detail["final_price"],
            "photo_s3_url": photo_s3_url,
            "check_image": check_image,
        }
    else:
        return {
            "name": "Продукт недоступен",
            "description": "Информация о продукте временно недоступна.",
            "price": "—",
            "photo_s3_url": None,
            "check_image": None,
        }


from aiogram_dialog.widgets.text import Multi

categories_window = Window(
    Multi(
        Const("📂 Категории"),
        Format("{error_message}", when="error_message"),
    ),
    ScrollingGroup(
        Select(
            Format("📁 {item[name]}"),
            id="categories_button",
            item_id_getter=lambda x: x["id"],
            items="categories",
            on_click=category_button,
        ),
        id="categories_scroll_menu",
        width=1,
        height=5,
        when=lambda data, *_: data["categories"] and len(data["categories"]) > 5,
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
        when=lambda data, *_: data["categories"] and len(data["categories"]) <= 5,
    ),
    Cancel(text=Const("🔙 Назад в Меню!"), id="__main__"),
    getter=categories_getter,
    state=ProductsSG.categories,
)

# Окно отображения продуктов
products_window = Window(
    Multi(
        Const("🍔 Продукты"),
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
        when=lambda data, *_: data["products"] and len(data["products"]) > 5,
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
        when=lambda data, *_: data["products"] and len(data["products"]) <= 5,
    ),
    SwitchTo(
        text=Const("🔙 Назад"),
        id="back_to_category",
        state=ProductsSG.categories,
    ),
    Cancel(text=Const("🔙 Назад в Меню!"), id="__main__"),
    getter=products_getter,
    state=ProductsSG.products,
)

# Окно отображения информации о продукте
product_detail_window = Window(
    StaticMedia(url=Format("{photo_s3_url}"), when="check_image"),
    Format("🏷️ Наименование: {name}"),
    Format("📝 Описание: {description}", when="description"),
    Format("💰 Цена: {price} руб."),
    Button(
        text=Const("🛒 Добавить в корзину"),
        id="add_to_cart",
        on_click=add_to_cart_button,
    ),
    SwitchTo(
        text=Const("🔙 Назад"),
        id="back_to_products",
        state=ProductsSG.products,
    ),
    Cancel(text=Const("🔙 Назад в Меню!"), id="__main__"),
    getter=product_detail_getter,
    state=ProductsSG.product_detail,
)


dialog = Dialog(categories_window, products_window, product_detail_window)
