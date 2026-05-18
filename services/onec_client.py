"""
HTTP-клиент для 1С с поддержкой расширенного каталога:
  • brands, categories, products, variants — раздельные эндпоинты
"""
import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

RETRY_DELAYS = [5, 15, 30]


class OneCError(Exception):
    pass


class ClientNotFound(OneCError):
    pass


class Client1C:
    def __init__(self, base_url: str, username: str, password: str, timeout: float = 30.0):
        self._base = base_url.rstrip("/")
        self._auth = (username, password)
        self._timeout = timeout

    # ─── Клиенты ──────────────────────────────────────────────────────────

    async def check_client_by_inn(self, inn: str) -> dict:
        try:
            data = await self._get(f"/hs/clients/check?inn={inn}")
        except OneCError:
            raise
        if not data.get("found"):
            raise ClientNotFound(f"ИНН {inn} не найден в 1С")
        return data

    # ─── Заказы ───────────────────────────────────────────────────────────

    async def create_order_with_invoice(self, payload: dict) -> dict:
        return await self._post("/hs/orders/create-with-invoice", payload)

    async def get_payment_status(self, one_c_order_id: str) -> dict:
        return await self._get(f"/hs/orders/{one_c_order_id}/payment-status")

    async def get_order_statuses(self, order_ids: list[str]) -> dict[str, str]:
        return await self._post("/hs/orders/statuses", {"ids": order_ids})

    # ─── Каталог ──────────────────────────────────────────────────────────

    async def get_brands(self) -> list[dict]:
        return await self._get("/hs/catalog/brands")

    async def get_categories(self) -> list[dict]:
        return await self._get("/hs/catalog/categories")

    async def get_products(self) -> list[dict]:
        return await self._get("/hs/catalog/products")

    async def get_variants(self) -> list[dict]:
        return await self._get("/hs/catalog/variants")

    async def get_stock(self) -> list[dict]:
        return await self._get("/hs/catalog/stock")

    # ─── Внутренние методы ─────────────────────────────────────────────────

    async def _get(self, path: str) -> Any:
        return await self._request("GET", path)

    async def _post(self, path: str, body: dict) -> Any:
        return await self._request("POST", path, json=body)

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        url = self._base + path
        last_exc: Exception | None = None

        for attempt, delay in enumerate([0] + RETRY_DELAYS, start=1):
            if delay:
                logger.warning("Retry %d for %s %s in %ds", attempt, method, path, delay)
                await asyncio.sleep(delay)
            try:
                async with httpx.AsyncClient(
                    auth=self._auth, timeout=self._timeout,
                    headers={"Accept": "application/json; charset=utf-8"},
                ) as client:
                    resp = await client.request(method, url, **kwargs)
                    resp.raise_for_status()
                    return resp.json()
            except httpx.HTTPStatusError as exc:
                msg = f"HTTP {exc.response.status_code}: {exc.request.url}"
                logger.error(msg)
                last_exc = OneCError(msg)
                if exc.response.status_code < 500:
                    break
            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                logger.warning("1С недоступна: %s", exc)
                last_exc = OneCError(f"1С недоступна: {exc}")
            except Exception as exc:
                logger.exception("Неожиданная ошибка обращения к 1С")
                last_exc = OneCError(str(exc))
                break

        raise last_exc or OneCError("Неизвестная ошибка")
