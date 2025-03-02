import jwt
from datetime import datetime, timedelta
from environs import Env


env = Env()
env.read_env()


SECRET_KEY_BOT = env("SECRET_KEY_BOT")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(tg_id: str):
    to_encode = {"tg_id": tg_id}
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY_BOT, algorithm=ALGORITHM)
    return encoded_jwt
