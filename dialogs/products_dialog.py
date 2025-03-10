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


# Хэндлер для добавления продукта в корзину
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
        await api.post(
            "/carts/add/",
            data=data,
        )
    await callback.answer(f"{product_name} добавлен(а) в корзину")


# Геттер для получения всех категорий и передаче в окно
async def categories_getter(dialog_manager: DialogManager, **kwargs):
    async with APIClient() as api:
        categories = await api.get("/category/")
        return {"categories": categories}


# Геттер для получения всех продуктов этой категории и передаче в окно
async def products_getter(dialog_manager: DialogManager, **kwargs):
    category_id = dialog_manager.dialog_data["category_id"]
    async with APIClient() as api:
        products = await api.get(f"/products/?category_id={category_id}")
        return {"products": products}


# Гетер для получения информации о продукте и передаче в окно
async def product_detail_getter(dialog_manager: DialogManager, **kwargs):
    product_id = dialog_manager.dialog_data["product_id"]
    async with APIClient() as api:
        product_detail = await api.get(f"/products/{product_id}/")
        dialog_manager.dialog_data["product_name"] = product_detail["name"]
        check_image = product_detail["photo_url"]
        photo_s3_url = None
        if check_image:
            photo_s3_url = (
                f"{env('S3_HOST')}{env('S3_BACKET')}{product_detail['photo_url']}"
            )
        return {
            "name": product_detail["name"],
            "description": product_detail["description"],
            "price": product_detail["final_price"],
            "photo_s3_url": photo_s3_url,
            "check_image": check_image,
        }


# Окно отображения категорий
categories_window = Window(
    Const("📂 Категории"),
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
        when=lambda data, *_: len(data["categories"]) > 5,
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
        when=lambda data, *_: len(data["categories"]) <= 5,
    ),
    Cancel(text=Const("🔙 Назад в Меню!"), id="__main__"),
    getter=categories_getter,
    state=ProductsSG.categories,
)

# Окно отображения продуктов
products_window = Window(
    Const("🍔 Продукты"),
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
        when=lambda data, *_: len(data["products"]) > 5,
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
        when=lambda data, *_: len(data["products"]) <= 5,
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
    Format("💰 Цена: {price} ₽"),
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
