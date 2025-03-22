from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    DOCKER_HUB_USERNAME: str
    BOT_TOKEN: str

    SECRET_KEY_BOT: str
    ALGORITHM: str = "HS256"

    S3_HOST: str
    S3_BACKET: str

    API_HOST: str
    API_PORT: int

    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    REDIS_HOST: str
    REDIS_PORT: int

    RMQ_HOST: str
    RMQ_PORT: str
    RMQ_USER: str
    RMQ_PASSWORD: str

    GRAFANA_USER: str
    GRAFANA_PASSWORD: str

    MAIN_MENU_BOT: dict = {
        "/start": "Старт бота и регистрация",
        "/menu": "Главное меню",
        "/help": "Техническая поддержка",
    }

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
