# Smart Storage

Telegram Mini App для перекупщиков смартфонов: приём телефонов у клиентов, продажи, склады, сотрудники и отчёты о проданных и непроданных телефонах.

- `backend/`: Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL, бот на aiogram
- `frontend/`: React, TypeScript, Vite, TanStack Query

## Возможности

- Несколько независимых магазинов в одном приложении. Любой пользователь Telegram может создать свой магазин и стать владельцем.
- В магазине несколько складов и сотрудников с ролями: владелец, менеджер, продавец. Продавец не видит закупочные цены и прибыль.
- Две валюты: UZS и USD. Суммы в отчётах считаются отдельно по каждой валюте.
- Приём телефона вместе с покупкой у клиента, расходы на ремонт, продажа, возврат.
- Отчёты: сводка, проданные за период с прибылью, непроданные с количеством дней на складе.

## Запуск backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env          # укажите BOT_TOKEN, JWT_SECRET, DATABASE_URL
alembic upgrade head
uvicorn app.main:app --reload # API и Swagger: http://localhost:8000/docs
python -m app.bot             # бот с кнопкой открытия Mini App
pytest                        # тесты (SQLite, без PostgreSQL)
```

Или всё вместе через Docker: `docker compose up --build` из корня (нужен `backend/.env`).

## Запуск frontend

```bash
cd frontend
npm install
cp .env.example .env   # VITE_API_URL=адрес backend
npm run dev
```

Вне Telegram приложение не может войти: для локальной разработки положите подписанную строку initData в `VITE_DEV_INIT_DATA` (её можно получить функцией `sign_init_data` в `backend/app/telegram_auth.py`).

Чтобы открыть приложение в Telegram, frontend должен быть доступен по HTTPS. Укажите этот адрес в `WEBAPP_URL` бота и в BotFather (Bot Settings → Menu Button).

## Как устроен API

- `POST /auth/telegram`: проверка подписи initData токеном бота, выдача JWT.
- Все запросы магазина передают заголовок `X-Shop-Id`. Backend проверяет, что пользователь состоит в этом магазине, и не отдаёт данные других магазинов.
- Полный список методов: `/docs` после запуска backend.
