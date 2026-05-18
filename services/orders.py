"""
Сервис создания заказа.
Создаём заказ в БД → отправляем в 1С → получаем счёт и договор → шлём клиенту.
"""
import logging
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Order, OrderItem, CartItem, Organization, User, Product
from services.onec_client import Client1C, OneCError

logger = logging.getLogger(__name__)


class OrderCreationError(Exception):
    pass


async def create_order_from_cart(
    db: AsyncSession,
    onec: Client1C,
    user: User,
    organization: Organization,
    comment: str = "",
) -> Order:
    """
    1. Берём корзину
    2. Создаём Order + OrderItems в БД (status=draft)
    3. Отправляем в 1С (метод create_order_with_invoice)
    4. Получаем invoice_url, contract_url, invoice_number
    5. Сохраняем эти поля, переводим статус → invoiced
    6. Очищаем корзину
    """
    # ── 1. Корзина ──
    result = await db.execute(
        select(CartItem).where(CartItem.user_id == user.id)
    )
    cart_items = result.scalars().all()
    if not cart_items:
        raise OrderCreationError("Корзина пуста")

    # Подгружаем товары
    product_ids = [c.product_id for c in cart_items]
    result = await db.execute(select(Product).where(Product.id.in_(product_ids)))
    products = {p.id: p for p in result.scalars().all()}

    # ── 2. Заказ в БД ──
    order = Order(
        user_id=user.id,
        org_id=organization.id,
        status="draft",
        comment=comment,
    )
    db.add(order)
    await db.flush()

    total = Decimal(0)
    items_for_1c = []

    for ci in cart_items:
        product = products[ci.product_id]
        subtotal = product.price * ci.quantity

        item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=ci.quantity,
            unit_price=product.price,
            subtotal=subtotal,
        )
        db.add(item)
        total += subtotal

        items_for_1c.append({
            "sku": product.sku,
            "one_c_id": product.one_c_id,
            "name": product.name,
            "qty": ci.quantity,
            "unit_price": float(product.price),
            "subtotal": float(subtotal),
        })

    order.total_amount = total
    order.status = "pending_1c"
    await db.flush()

    # ── 3. Отправка в 1С ──
    payload = {
        "external_ref":      order.id,
        "client_one_c_id":   organization.one_c_id,
        "client_inn":        organization.inn,
        "items":             items_for_1c,
        "total":             float(total),
        "comment":           comment,
    }

    try:
        result = await onec.create_order_with_invoice(payload)
    except OneCError as exc:
        logger.error("Failed to create order in 1С: %s", exc)
        order.status = "draft"  # откатываем статус, заказ можно повторно отправить
        await db.commit()
        raise OrderCreationError(
            "Не удалось создать заказ в 1С. "
            "Попробуйте позже или свяжитесь с менеджером."
        )

    # ── 4-5. Сохраняем результат от 1С ──
    order.one_c_id        = result.get("one_c_id")
    order.invoice_number  = result.get("invoice_number")
    order.invoice_url     = result.get("invoice_url")
    order.contract_url    = result.get("contract_url")
    order.synced_to_1c    = True
    order.status          = "invoiced"

    # Если 1С пересчитала тотал — обновляем
    if "total_amount" in result:
        order.total_amount = Decimal(str(result["total_amount"]))

    # ── 6. Очищаем корзину ──
    for ci in cart_items:
        await db.delete(ci)

    await db.commit()
    await db.refresh(order)
    return order
