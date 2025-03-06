from aiogram.types import Message
from aiogram_dialog import DialogManager, Dialog, Window
from aiogram_dialog.widgets.text import Const
from aiogram_dialog.widgets.input import TextInput, ManagedTextInput
from email_validator import validate_email, EmailNotValidError
from states import StartState, MenuState
from services.api_client import APIClient
from db.operations import UserDO


# Функция проверки валидности email
def check_email(email: str):
    try:
        validate_email(email)
        return email
    except EmailNotValidError:
        raise


# Хэндлер регистрации пользователя
async def correct_email(
    message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str
):
    session = dialog_manager.middleware_data["session"]
    tg_id = str(message.from_user.id)
    data = {
        "email": text,
        "tg_id": tg_id,
    }
    db_user = UserDO.get_by_email(email=text, session=session)
    if db_user:
        await message.answer("Пользователь с такой почтой уже присутствует!")
        await dialog_manager.switch_to(state=StartState.start)
    else:
        async with APIClient() as api:
            result = await api.post("/users/register/", data=data)
            await UserDO.add(session=session, **{"tg_id": tg_id, "email": text})
            await dialog_manager.start(state=MenuState.menu)


# Хэндлер для обработки невалидного email
async def incorrect_email(
    message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str
):
    await message.answer("Введена некорректная почта!")
    await dialog_manager.switch_to(state=StartState.start)


start_window = Window(
    Const("Введи свою почту"),
    TextInput(
        id="email_input",
        type_factory=check_email,
        on_success=correct_email,
        on_error=incorrect_email,
    ),
    state=StartState.start,
)


dialog = Dialog(start_window)
