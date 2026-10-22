import pytest

from app.admin import VIEWS
from tests.test_flow import buy


def admin_login(client, password="admin-test-password"):
    return client.post(
        "/admin/login", data={"username": "admin", "password": password}, follow_redirects=False
    )


def test_admin_requires_login(client):
    res = client.get("/admin/", follow_redirects=False)
    assert res.status_code in (302, 303)
    assert "/admin/login" in res.headers["location"]


def test_admin_wrong_password(client):
    assert admin_login(client, "wrong").status_code == 400


@pytest.mark.parametrize("view", VIEWS, ids=lambda v: v.identity)
def test_admin_pages_open(client, owner, view):
    phone = buy(client, owner).json()
    h = owner["headers"]
    client.post(f"/phones/{phone['id']}/expenses", json={"amount": "1", "currency": "UZS", "description": "x"}, headers=h)
    client.post(f"/phones/{phone['id']}/sell", json={"price": "2", "currency": "UZS"}, headers=h)
    assert admin_login(client).status_code in (302, 303)
    res = client.get(f"/admin/{view.identity}/list")
    assert res.status_code == 200, res.text
    res = client.get(f"/admin/{view.identity}/details/1")
    assert res.status_code == 200, res.text
    if view.can_edit:
        assert client.get(f"/admin/{view.identity}/edit/1").status_code == 200
