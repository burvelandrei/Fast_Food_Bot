from pydantic_settings import BaseSettings

class Settings(BaseSettings):
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

    RMQ_USER: str
    RMQ_PASSWORD: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()