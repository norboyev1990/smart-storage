from app.telegram_auth import InitDataError, validate_init_data
from tests.conftest import init_data_for


def test_valid_init_data():
    user = validate_init_data(init_data_for(42), "123456:TEST", 3600)
    assert user["id"] == 42


def test_tampered_init_data_is_rejected():
    data = init_data_for(42).replace("42", "43")
    try:
        validate_init_data(data, "123456:TEST", 3600)
    except InitDataError:
        return
    raise AssertionError("tampered initData accepted")


def test_login_and_me(client):
    res = client.post("/auth/telegram", json={"init_data": init_data_for(7, "Ali")})
    assert res.status_code == 200
    token = res.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
    assert me["telegram_id"] == 7 and me["first_name"] == "Ali"


def test_bad_login(client):
    assert client.post("/auth/telegram", json={"init_data": "user=1&hash=bad"}).status_code == 401
