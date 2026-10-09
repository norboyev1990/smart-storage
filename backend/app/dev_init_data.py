"""Print a signed initData for local testing outside Telegram.

Usage: python -m app.dev_init_data [telegram_id] [first_name]
Put the output into VITE_DEV_INIT_DATA in frontend/.env.
"""
import json
import sys
import time

from app.config import get_settings
from app.telegram_auth import sign_init_data


def main() -> None:
    telegram_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    first_name = sys.argv[2] if len(sys.argv) > 2 else "Dev"
    settings = get_settings()
    if not settings.bot_token:
        sys.exit("BOT_TOKEN is not set in backend/.env")
    fields = {
        "auth_date": str(int(time.time())),
        "user": json.dumps({"id": telegram_id, "first_name": first_name}),
    }
    print(sign_init_data(fields, settings.bot_token))


if __name__ == "__main__":
    main()
