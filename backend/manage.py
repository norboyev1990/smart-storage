"""Server tasks for hosting without a shell-friendly setup (cPanel "Execute python script").

    python manage.py migrate       # alembic upgrade head
    python manage.py set-webhook   # point the bot at {API_URL}/telegram/webhook
"""
import asyncio
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))


def migrate() -> None:
    from alembic.config import main

    main(["upgrade", "head"])
    print("Migrations applied")


def set_webhook() -> None:
    from app.bot import set_webhook as run

    print("Webhook set:", asyncio.run(run()))


COMMANDS = {"migrate": migrate, "set-webhook": set_webhook}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        sys.exit(f"Usage: python manage.py {{{'|'.join(COMMANDS)}}}")
    COMMANDS[sys.argv[1]]()
