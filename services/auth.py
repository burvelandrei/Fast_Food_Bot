import jwt
from datetime import datetime, timedelta
from config import settings


ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(email: str):
    """Функция создания access токена"""
    to_encode = {"email": email}
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY_BOT,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt
