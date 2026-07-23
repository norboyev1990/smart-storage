# smart-storage

Store balance app — Telegram Mini App backend built with Django and Django REST Framework.

## Features

- **Users** — Telegram user management (buyer / seller roles)
- **Products** — Inventory with IMEI tracking, pricing, and photo support
- **Reports** — Remaining items and sold items reports via REST API

## Models

### `TelegramUser`
| Field | Type | Notes |
|---|---|---|
| `username` | CharField | Telegram username |
| `first_name` | CharField | |
| `last_name` | CharField | |
| `telegram_id` | BigIntegerField | Unique Telegram user ID |
| `phone_number` | CharField | Optional |

### `Product`
| Field | Type | Notes |
|---|---|---|
| `product_name` | CharField | |
| `income_price` | DecimalField | Purchase cost |
| `imei_code` | CharField | Optional IMEI / serial number |
| `photo` | ImageField | Uploaded to `media/products/` |
| `buyer` | FK → TelegramUser | Nullable |
| `seller` | FK → TelegramUser | Nullable |
| `purchase_date` | DateField | |
| `sold_date` | DateField | Nullable |
| `is_sold` | BooleanField | `False` = in stock |

## API Endpoints

| Method | URL | Description |
|---|---|---|
| GET/POST | `/api/users/` | List / create users |
| GET/PUT/DELETE | `/api/users/{id}/` | Retrieve / update / delete user |
| GET/POST | `/api/products/` | List / create products |
| GET/PUT/DELETE | `/api/products/{id}/` | Retrieve / update / delete product |
| GET | `/api/reports/remaining/` | Remaining (unsold) items |
| GET | `/api/reports/sold/` | Sold items |

## Setup

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Access the Django admin at `http://localhost:8000/admin/`.
