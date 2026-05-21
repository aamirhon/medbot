"""
Сервис создания заказа.

SQL-миграции (если OrderItem был создан без снимочных полей):
  ALTER TABLE order_items ADD COLUMN product_name VARCHAR(255) DEFAULT '';
  ALTER TABLE order_items ADD COLUMN pack_size VARCHAR(100) DEFAULT '';
  ALTER TABLE order_items ADD COLUMN sku VARCHAR(100) DEFAULT '';

В текущей модели эти поля уже есть — миграция не требуется.
"""
import logging
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    Order, OrderItem, OrderEvent,
    CartItem, ProductVariant, Product,
    Organization, User,
)
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
    # 1. Корзина
    cart_result = await db.execute(
        select(CartItem, ProductVariant, Product)
        .join(ProductVariant, CartItem.variant_id == ProductVariant.id)
        .join(Product, ProductVariant.product_id == Product.id)
        .where(CartItem.user_id == user.id)
    )
    rows = cart_result.all()
    if not rows:
        raise OrderCreationError("Корзина пуста")

    # 2. Валидация
    for ci, variant, product in rows:
        if not variant.is_orderable:
            raise OrderCreationError(
                "В корзине есть товары 'по запросу'. Удалите их перед оформлением."
            )
        if ci.quantity > variant.stock_qty:
            raise OrderCreationError(
                f"Недостаточно товара на складе: {product.name} ({variant.pack_size}). "
                f"Доступно: {variant.stock_qty}"
            )

    # 3. Создать Order
    order = Order(
        user_id=user.id,
        org_id=organization.id,
        status="draft",
        comment=comment,
    )
    db.add(order)
    await db.flush()

    # 4. Создать OrderItem со снимком данных
    total = Decimal(0)
    for ci, variant, product in rows:
        unit_price = variant.price or Decimal(0)
        subtotal = unit_price * ci.quantity
        db.add(OrderItem(
            order_id=order.id,
            variant_id=variant.id,
            product_name=product.name,
            pack_size=variant.pack_size,
            sku=variant.sku,
            quantity=ci.quantity,
            unit_price=unit_price,
            subtotal=subtotal,
        ))
        total += subtotal

    # 5. Итог
    order.total_amount = total
    order.status = "pending_1c"
    await db.flush()

    # 6. Payload для 1С
    items_for_1c = [
        {
            "variant_one_c_id": variant.one_c_id,
            "product_one_c_id": product.one_c_id,
            "sku": variant.sku,
            "name": f"{product.name} ({variant.pack_size})",
            "qty": ci.quantity,
            "unit_price": float(variant.price or 0),
            "subtotal": float((variant.price or 0) * ci.quantity),
        }
        for ci, variant, product in rows
    ]

    payload = {
        "external_ref":    order.id,
        "client_one_c_id": organization.one_c_id,
        "client_inn":      organization.inn,
        "items":           items_for_1c,
        "total":           float(order.total_amount),
        "comment":         comment,
    }

    # 7. Отправить в 1С
    try:
        result_1c = await onec.create_order_with_invoice(payload)
    except OneCError as exc:
        logger.error("Failed to create order in 1С: %s", exc)
        order.status = "draft"
        await db.commit()
        raise OrderCreationError("Не удалось создать заказ в 1С. Попробуйте позже.")

    order.one_c_id       = result_1c.get("one_c_id")
    order.invoice_number = result_1c.get("invoice_number")
    order.invoice_url    = result_1c.get("invoice_url")
    order.contract_url   = result_1c.get("contract_url")
    order.synced_to_1c   = True
    order.synced_at      = datetime.now(timezone.utc)
    order.status         = "invoiced"

    # 8. Очистить корзину
    await db.execute(delete(CartItem).where(CartItem.user_id == user.id))

    # 9. Событие
    db.add(OrderEvent(
        order_id=order.id,
        event_type="created",
        payload={"description": "Заказ создан и отправлен в 1С"},
    ))

    # 10. Сохранить
    await db.commit()
    await db.refresh(order)
    return order
