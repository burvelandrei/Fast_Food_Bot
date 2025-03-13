from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Start, Cancel
from dialogs.states import HistoryOrdersSG, ProfileSG, CurrentOrdersSG
from services.api_client import APIClient, APIError
from db.operations import UserDO


# Гуттер для получения данных о пользоваетеле и передаче в окно профиля
async def profile_getter(dialog_manager: DialogManager, **kwargs):
    tg_id = str(dialog_manager.event.from_user.id)
    session = dialog_manager.middleware_data["session"]
    user = await UserDO.get_by_tg_id(tg_id=tg_id, session=session)
    try:
        async with APIClient(user.email) as api:
            profile = await api.get("/users/profile/")
            return {
                "email": profile["email"],
                "tg_id": profile["tg_id"],
                "error_message": None,
            }
    except APIError:
        error_message = "Профиль юзера временно недоступен"
        return {
            "email": "-",
            "tg_id": "-",
            "error_message": error_message,
        }


# Окно отображения профиля юзера
profile_window = Window(
    Const("👤 Мой профиль"),
    Format("{error_message}", when="error_message"),
    Format("\nEmail: {email}"),
    Format("Telegram_ID: {tg_id}"),
    Start(
        Const("⏳ Текущие заказы"),
        id="current_orders",
        state=CurrentOrdersSG.orders,
    ),
    Start(
        Const("📜 История заказов"),
        id="history_orders",
        state=HistoryOrdersSG.orders,
    ),
    Cancel(
        text=Const("🔙 Назад в Меню!"),
        id="__menu__",
    ),
    getter=profile_getter,
    state=ProfileSG.profile,
)


dialog = Dialog(profile_window)
