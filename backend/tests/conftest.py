import json
import os
import time

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["BOT_TOKEN"] = "123456:TEST"
os.environ["JWT_SECRET"] = "test-secret-key-that-is-long-enough-123"

import pytest
from fastapi.testclient import TestClient

from app.db import Base, engine
from app.main import app
from app.telegram_auth import sign_init_data


@pytest.fixture(autouse=True)
def db_schema():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def client():
    return TestClient(app)


def init_data_for(telegram_id: int, first_name: str = "Test") -> str:
    fields = {
        "auth_date": str(int(time.time())),
        "query_id": "AAH",
        "user": json.dumps({"id": telegram_id, "first_name": first_name}),
    }
    return sign_init_data(fields, os.environ["BOT_TOKEN"])


def login(client: TestClient, telegram_id: int) -> dict:
    res = client.post("/auth/telegram", json={"init_data": init_data_for(telegram_id)})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture
def owner(client):
    """An owner with a fresh shop. Returns headers including X-Shop-Id and the default warehouse id."""
    headers = login(client, 1001)
    shop = client.post("/shops", json={"name": "Shop A"}, headers=headers).json()
    headers["X-Shop-Id"] = str(shop["id"])
    warehouse = client.get("/warehouses", headers=headers).json()[0]
    return {"headers": headers, "shop_id": shop["id"], "warehouse_id": warehouse["id"]}
