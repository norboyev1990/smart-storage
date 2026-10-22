from unittest.mock import patch

from app.config import get_settings


def test_webhook_rejects_bad_secret(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "webhook_secret", "s3cret")
    assert client.post("/telegram/webhook", json={}).status_code == 403
    assert client.post("/telegram/webhook", json={}, headers={"X-Telegram-Bot-Api-Secret-Token": "nope"}).status_code == 403


def test_webhook_disabled_without_secret(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "webhook_secret", "")
    assert client.post("/telegram/webhook", json={}, headers={"X-Telegram-Bot-Api-Secret-Token": ""}).status_code == 403


def test_webhook_feeds_update(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "webhook_secret", "s3cret")
    with patch("app.bot.process_update") as process:
        res = client.post("/telegram/webhook", json={"update_id": 1}, headers={"X-Telegram-Bot-Api-Secret-Token": "s3cret"})
    assert res.status_code == 200
    process.assert_awaited_once_with({"update_id": 1})
