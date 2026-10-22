from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.admin import mount_admin
from app.config import get_settings
from app.routers import auth, clients, phones, reports, shops, telegram

app = FastAPI(title="Smart Storage API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (auth, shops, clients, phones, reports, telegram):
    app.include_router(module.router)

mount_admin(app)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
