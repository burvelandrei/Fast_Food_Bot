from aiogram.types import Message, CallbackQuery
from aiogram_dialog import DialogManager, Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Button, SwitchTo, Select, Cancel, ScrollingGroup
from aiogram_dialog.widgets.media import StaticMedia
from environs import Env
from states import ProductsState
from services.api_client import APIClient
from db.operations import UserDO


env = Env()
env.read_env()


async def category_button(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
):
    dialog_manager.dialog_data["category_id"] = item_id
    await dialog_manager.switch_to(state=ProductsState.products)


async def product_button(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
):
    dialog_manager.dialog_data["product_id"] = item_id
    await dialog_manager.switch_to(state=ProductsState.product_detail)


async def add_to_cart_button(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
):
    tg_id = str(callback.from_user.id)
    session = dialog_manager.middleware_data["session"]
    user = await UserDO.get_by_tg_id(tg_id=tg_id, session=session)
    product_id = dialog_manager.dialog_data["product_id"]
    async with APIClient(user.email) as api:
        await api.post("/carts/add/", data={"product_id": product_id, "quantity": 1})
    await callback.answer("Добавлено в корзину")


async def categories_getter(dialog_manager: DialogManager, **kwargs):
    async with APIClient() as api:
        categories = await api.get("/category/")
        return {"categories": categories}


async def products_getter(dialog_manager: DialogManager, **kwargs):
    category_id = dialog_manager.dialog_data["category_id"]
    async with APIClient() as api:
        products = await api.get(f"/products/?category_id={category_id}")
        return {"products": products}


async def product_detail_getter(dialog_manager: DialogManager, **kwargs):
    product_id = dialog_manager.dialog_data["product_id"]
    async with APIClient() as api:
        product_detail = await api.get(f"/products/{product_id}/")
        check_image = product_detail["image_url"]
        image_url = None
        if check_image:
            image_url = f"{env("S3_HOST")}{product_detail["image_url"]}"
        return {
            "name": product_detail["name"],
            "description": product_detail["description"],
            "price": product_detail["final_price"],
            "image_url": image_url,
            "check_image": check_image,
        }


catgories_window = Window(
    Const("Категории"),
    Select(
        Format("{item[name]}"),
        id="categories_button",
        item_id_getter=lambda x: x["id"],
        items="categories",
        on_click=category_button,
    ),
    Cancel(text=Const("🔙 Назад в Меню!"), id="__main__"),
    getter=categories_getter,
    state=ProductsState.categories,
)


products_window = Window(
    Const("Продукт"),
    Select(
        Format("{item[name]}"),
        id="products_button",
        item_id_getter=lambda x: x["id"],
        items="products",
        on_click=product_button,
    ),
    SwitchTo(
        text=Const("🔙 Назад"),
        id="back_to_category",
        state=ProductsState.categories,
    ),
    Cancel(text=Const("🔙 Назад в Меню!"), id="__main__"),
    getter=products_getter,
    state=ProductsState.products,
)


product_detail_window = Window(
    StaticMedia(url=Format("{image_url}"), when="check_image"),
    Format("Наименование: {name}"),
    Format("Описание: {description}", when="description"),
    Format("Цена: {price}"),
    Button(
        text=Const("Добавить в корзину"),
        id="add_to_cart",
        on_click=add_to_cart_button,
    ),
    SwitchTo(
        text=Const("🔙 Назад"),
        id="back_to_products",
        state=ProductsState.products,
    ),
    Cancel(text=Const("🔙 Назад в Меню!"), id="__main__"),
    getter=product_detail_getter,
    state=ProductsState.product_detail,
)

dialog = Dialog(catgories_window, products_window, product_detail_window)
