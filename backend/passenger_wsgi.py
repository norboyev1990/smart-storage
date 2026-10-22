"""Entry point for cPanel "Setup Python App" (Phusion Passenger speaks WSGI, FastAPI is ASGI)."""
from a2wsgi import ASGIMiddleware

from app.main import app

application = ASGIMiddleware(app)
