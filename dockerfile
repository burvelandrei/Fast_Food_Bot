FROM python:3.12

COPY requirements.txt .

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD ["sh", "-c", "sleep 10 && alembic upgrade head && python bot.py"]