import logging
import logging.config
from typing import Optional, Dict, Any
from environs import Env
from aiohttp import client
from services.auth import create_access_token
from utils.logger import logging_config


env = Env()
env.read_env()


logging.config.dictConfig(logging_config)
logger = logging.getLogger(__name__)


class APIError(Exception):
    """Базовое исключение для ошибок API."""

    pass


class APIClient:
    """Класс для запросов к API."""

    def __init__(self, email: Optional[str] = None):
        self.domain = f"http://{env('API_HOST')}:{env('API_PORT')}"
        self.headers = {"Content-Type": "application/json"}
        if email:
            self.access_token = create_access_token(email)
            self.headers["Authorization"] = f"Bearer {self.access_token}"

    async def __aenter__(self):
        self.session = client.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def get(self, endpoint: str):
        url = self.domain + endpoint
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    logger.info(f"GET request successful: {response.status}")
                    return await response.json()
                else:
                    logger.error(f"GET request failed - Status: {response.status}")
                    raise APIError(f"API request failed with status {response.status}")
        except client.ClientError as e:
            logger.error(f"Network error - {e}")
            raise APIError(f"Network error: {e}")

    async def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None):
        url = self.domain + endpoint
        try:
            async with self.session.post(url, json=data) as response:
                if response.status in {200, 201}:
                    logger.info(f"POST request successful: {response.status}")
                    return await response.json()
                else:
                    logger.error(f"POST request failed - Status: {response.status}")
                    raise APIError(f"API request failed with status {response.status}")
        except client.ClientError as e:
            logger.error(f"Network error - {e}")
            raise APIError(f"Network error: {e}")

    async def delete(self, endpoint: str):
        url = self.domain + endpoint
        try:
            async with self.session.delete(url) as response:
                if response.status == 200:
                    logger.info(f"DELETE request successful: {response.status}")
                    return await response.json()
                else:
                    logger.error(f"DELETE request failed - Status: {response.status}")
                    raise APIError(f"API request failed with status {response.status}")
        except client.ClientError as e:
            logger.error(f"Network error - {e}")
            raise APIError(f"Network error: {e}")
