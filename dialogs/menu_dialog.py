from aiogram.types import Message
from aiogram_dialog import DialogManager, Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Button, SwitchTo, Start
from aiogram_dialog.widgets.input import TextInput, ManagedTextInput
from email_validator import validate_email, EmailNotValidError
from states import StartState, MenuState, ProductsState
from services.api_client import APIClient


menu_window = Window(
    Const("Меню"),
    Start(
        Const("Список продуктов"),
        id="list_productds",
        state=ProductsState.categories,
    ),
    state=MenuState.menu,
)


dialog = Dialog(menu_window)
