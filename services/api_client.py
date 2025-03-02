import asyncio
from environs import Env
from aiohttp import client
from services.auth import create_access_token

env = Env()
env.read_env()


class APIClient:
    def __init__(self, access_token: str = None):
        self.domain = f"http://{env('API_HOST')}:{env('API_PORT')}"
        self.access_token = access_token
        self.headers = {"Content-Type": "application/json"}
        if self.access_token:
            self.headers["Authorization"] = f"Bearer {self.access_token}"

    async def __aenter__(self):
        self.session = client.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def get(self, endpoint):
        url = self.domain + endpoint
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    print(response.status)
                    print(await response.json())
                else:
                    print(f"Ошибка GET запроса - {response.status}")
        except client.ClientError as e:
            print(f"Ошибка сети - {e}")

    async def post(self, endpoint, data):
        url = self.domain + endpoint
        try:
            async with self.session.post(url, json=data) as response:
                if response.status in {200, 201}:
                    print(response.status)
                    print(await response.json())
                else:
                    print(
                        f"Ошибка POST запроса - {response.status}, {await response.json()}"
                    )
        except client.ClientError as e:
            print(f"Ошибка сети - {e}")

    async def delete(self, endpoint):
        url = self.domain + endpoint
        try:
            async with self.session.delete(url) as response:
                if response.status == 200:
                    print(response.status)
                    print(await response.json())
                else:
                    print(f"Ошибка DELETE запроса - {response.status}")
        except client.ClientError as e:
            print(f"Ошибка сети - {e}")


async def main():
    access_token = create_access_token("474528766")
    async with APIClient(access_token=access_token) as api:
        # await asyncio.create_task(api.get("/products"))
        # await asyncio.create_task(
        #     api.post(
        #         "/users/register",
        #         data={
        #             "email": "burvelandrei@gmail.com",
        #             "tg_id": "474528766",
        #         },
        #     )
        # )

        await api.post("/carts/add", {"product_id": 1, "quantity": 1})


if __name__ == "__main__":
    asyncio.run(main())
