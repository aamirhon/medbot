"""
FastAPI бэкенд для Mini App.
Запуск: uvicorn api.main:app --host 0.0.0.0 --port 8002
"""
import logging

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from api.auth import get_current_user
from api.routers import catalog, cart, orders
from models import User, Organization
from db import get_session

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Albatros Mini App API", version="1.0.0")

# CORS — разрешаем запросы с фронтенда (Telegram WebApp)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # для прода ограничить доменом WebApp
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(catalog.router)
app.include_router(cart.router)
app.include_router(orders.router)


# ─── Auth check / user info ──────────────────────────────────────────────────

class MeOut(BaseModel):
    user_id: str
    first_name: str
    role: str
    organization: dict
    has_limits: bool   # ограниченным показываем подсказку


@app.get("/me", response_model=MeOut)
async def me(user: User = Depends(get_current_user)):
    """Текущий пользователь и его организация. Уровень не отдаём."""
    async with get_session() as db:
        org = await db.get(Organization, user.org_id)

    return MeOut(
        user_id=user.id,
        first_name=user.first_name,
        role=user.role,
        organization={
            "id": org.id,
            "name": org.name,
            "inn": org.inn,
            "type": org.type,
        },
        has_limits=(org.client_tier == "limited"),
    )


@app.get("/health")
async def health():
    return {"status": "ok"}
