from tests.conftest import login

PHONE = {
    "brand": "Apple",
    "model": "iPhone 13",
    "storage_gb": 128,
    "imei1": "356789012345678",
    "condition": "good",
    "asking_price": "6500000",
    "asking_currency": "UZS",
}


def buy(client, owner, imei=PHONE["imei1"], price="5000000", currency="UZS"):
    body = {
        **PHONE,
        "imei1": imei,
        "warehouse_id": owner["warehouse_id"],
        "purchase": {"price": price, "currency": currency, "client": {"full_name": "Seller One"}},
    }
    return client.post("/phones", json=body, headers=owner["headers"])


def test_buy_sell_and_reports(client, owner):
    h = owner["headers"]
    res = buy(client, owner)
    assert res.status_code == 201, res.text
    phone = res.json()
    assert phone["status"] == "in_stock"
    assert phone["purchase"]["client"]["full_name"] == "Seller One"

    assert buy(client, owner).status_code == 409  # same IMEI already in stock

    client.post(f"/phones/{phone['id']}/expenses", json={"amount": "300000", "currency": "UZS", "description": "screen"}, headers=h)

    summary = client.get("/reports/summary", headers=h).json()
    assert summary["in_stock_count"] == 1
    assert summary["in_stock_cost"] == [{"currency": "UZS", "amount": "5300000.00"}]

    sale = client.post(f"/phones/{phone['id']}/sell", json={"price": "6500000", "currency": "UZS"}, headers=h)
    assert sale.status_code == 201, sale.text
    assert client.post(f"/phones/{phone['id']}/sell", json={"price": "1", "currency": "UZS"}, headers=h).status_code == 409

    sold = client.get("/reports/sold", headers=h).json()
    assert len(sold) == 1 and sold[0]["profit"] == "1200000.00"
    summary = client.get("/reports/summary", headers=h).json()
    assert summary["in_stock_count"] == 0 and summary["sold_count"] == 1
    assert summary["profit"] == [{"currency": "UZS", "amount": "1200000.00"}]

    cancel = client.post(f"/sales/{sale.json()['id']}/cancel", json={"reason": "returned"}, headers=h)
    assert cancel.status_code == 200
    assert client.get(f"/phones/{phone['id']}", headers=h).json()["status"] == "in_stock"
    assert client.get("/reports/sold", headers=h).json() == []


def test_two_currencies(client, owner):
    buy(client, owner, imei="111111111111111", price="400", currency="USD")
    buy(client, owner, imei="222222222222222", price="5000000", currency="UZS")
    totals = client.get("/reports/summary", headers=owner["headers"]).json()["in_stock_cost"]
    assert totals == [
        {"currency": "USD", "amount": "400.00"},
        {"currency": "UZS", "amount": "5000000.00"},
    ]


def test_shops_are_isolated(client, owner):
    phone = buy(client, owner).json()
    other = login(client, 2002)
    other_shop = client.post("/shops", json={"name": "Shop B"}, headers=other).json()
    other["X-Shop-Id"] = str(other_shop["id"])

    assert client.get(f"/phones/{phone['id']}", headers=other).status_code == 404
    assert client.get("/phones", headers=other).json()["total"] == 0
    # cannot pretend to be in someone else's shop
    other["X-Shop-Id"] = str(owner["shop_id"])
    assert client.get("/phones", headers=other).status_code == 403


def test_employees_and_roles(client, owner):
    h = owner["headers"]
    res = client.post("/members", json={"telegram_id": 3003, "role": "seller"}, headers=h)
    assert res.status_code == 201
    seller = login(client, 3003)
    seller["X-Shop-Id"] = str(owner["shop_id"])

    # seller works in the same warehouse
    phone = buy(client, {**owner, "headers": seller}).json()
    assert client.post(f"/phones/{phone['id']}/sell", json={"price": "6000000", "currency": "UZS"}, headers=seller).status_code == 201

    # but sees no profit and cannot manage members or cancel sales
    summary = client.get("/reports/summary", headers=seller).json()
    assert summary["profit"] is None
    assert client.get("/reports/sold", headers=seller).json()[0]["profit"] is None
    assert client.post("/members", json={"telegram_id": 4004}, headers=seller).status_code == 403

    # second warehouse
    assert client.post("/warehouses", json={"name": "Chilonzor"}, headers=h).status_code == 201
    assert len(client.get("/warehouses", headers=seller).json()) == 2
