from aiogram.types import Message
from aiogram_dialog import DialogManager, Dialog, Window
from aiogram_dialog.widgets.text import Const
from aiogram_dialog.widgets.input import TextInput, ManagedTextInput
from email_validator import validate_email, EmailNotValidError
from dialogs.states import StartSG
from services.api_client import APIClient, APIError
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
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    text: str,
):
    session = dialog_manager.middleware_data["session"]
    tg_id = str(message.from_user.id)
    data = {
        "email": text,
        "tg_id": tg_id,
    }
    db_user = await UserDO.get_by_email(email=text, session=session)
    if db_user:
        await message.answer("Пользователь с такой почтой уже присутствует!")
        await dialog_manager.switch_to(state=StartSG.input_email)
    else:
        try:
            async with APIClient() as api:
                await api.post("/users/register/", data=data)
                await message.answer(
                    "Для завершения регистрации, пожалуйста, подтвердите ваш"
                    " email, перейдя по ссылке в письме."
                )
                await dialog_manager.done()
        except APIError:
            await message.answer(
                "Произошла неизвестная ошибка. Давай попробуем ещё раз."
            )
            await dialog_manager.switch_to(state=StartSG.input_email)


# Хэндлер для обработки невалидного email
async def incorrect_email(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    text: str,
):
    await message.answer("Введена некорректная почта!")
    await dialog_manager.switch_to(state=StartSG.input_email)


input_email_window = Window(
    Const("Введи свою почту"),
    TextInput(
        id="input_email",
        type_factory=check_email,
        on_success=correct_email,
        on_error=incorrect_email,
    ),
    state=StartSG.input_email,
)


dialog = Dialog(input_email_window)
