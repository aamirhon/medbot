"""
Сервис проверки лимитов по уровню клиента.
Используется в корзине при добавлении/изменении товара.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from dataclasses import dataclass

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from models import TierLimit, Product, Order, OrderItem, Organization


@dataclass
class LimitCheckResult:
    ok: bool
    reason: str = ""
    max_allowed: int = 0


async def check_can_add_to_cart(
    db: AsyncSession,
    organization: Organization,
    product: Product,
    desired_qty: int,
) -> LimitCheckResult:
    """
    Проверяет, может ли клиент добавить такое количество товара в корзину
    с учётом его уровня и лимитов.
    """
    tier = organization.client_tier

    # 1. Лимит по категории (или дефолтный, если для категории нет правила)
    limit = await _get_tier_limit(db, tier, product.category_id)
    if not limit:
        # Нет правил — разрешаем всё
        return LimitCheckResult(ok=True)

    # 2. Проверка по количеству на один заказ
    if desired_qty > limit.max_qty_per_order:
        return LimitCheckResult(
            ok=False,
            reason=f"Лимит на одну заявку: {limit.max_qty_per_order} {product.unit}",
            max_allowed=limit.max_qty_per_order,
        )

    # 3. Проверка по количеству за месяц (по этой же категории)
    month_ago = datetime.now(timezone.utc) - timedelta(days=30)
    qty_this_month = await _get_qty_in_period(
        db, organization.id, product.category_id, month_ago
    )
    if qty_this_month + desired_qty > limit.max_qty_per_month:
        remaining = limit.max_qty_per_month - qty_this_month
        return LimitCheckResult(
            ok=False,
            reason=(
                f"Месячный лимит исчерпан. "
                f"За 30 дней заказано {qty_this_month}, "
                f"доступно ещё {max(remaining, 0)}"
            ),
            max_allowed=max(remaining, 0),
        )

    # 4. Проверка по сумме за месяц
    amount_this_month = await _get_amount_in_period(db, organization.id, month_ago)
    desired_amount = product.price * desired_qty
    if amount_this_month + desired_amount > limit.max_amount_per_month:
        return LimitCheckResult(
            ok=False,
            reason=(
                f"Превышен месячный лимит по сумме: "
                f"{limit.max_amount_per_month:,.0f} сум"
            ),
        )

    return LimitCheckResult(ok=True)


async def _get_tier_limit(
    db: AsyncSession, tier: str, category_id: str | None
) -> TierLimit | None:
    """Сначала ищем правило для категории, потом дефолтное."""
    if category_id:
        result = await db.execute(
            select(TierLimit).where(
                and_(TierLimit.tier == tier, TierLimit.category_id == category_id)
            )
        )
        cat_limit = result.scalar_one_or_none()
        if cat_limit:
            return cat_limit

    # Дефолтное правило (category_id IS NULL)
    result = await db.execute(
        select(TierLimit).where(
            and_(TierLimit.tier == tier, TierLimit.category_id.is_(None))
        )
    )
    return result.scalar_one_or_none()


async def _get_qty_in_period(
    db: AsyncSession,
    org_id: str,
    category_id: str | None,
    since: datetime,
) -> int:
    """Сколько товара этой категории заказано за период."""
    stmt = (
        select(func.coalesce(func.sum(OrderItem.quantity), 0))
        .join(Order, Order.id == OrderItem.order_id)
        .join(Product, Product.id == OrderItem.product_id)
        .where(
            Order.org_id == org_id,
            Order.status.in_(["pending_1c", "invoiced", "paid", "shipped", "delivered"]),
            Order.created_at >= since,
        )
    )
    if category_id:
        stmt = stmt.where(Product.category_id == category_id)
    result = await db.execute(stmt)
    return int(result.scalar() or 0)


async def _get_amount_in_period(
    db: AsyncSession, org_id: str, since: datetime
) -> Decimal:
    """Сумма заказов клиента за период."""
    result = await db.execute(
        select(func.coalesce(func.sum(Order.total_amount), 0))
        .where(
            Order.org_id == org_id,
            Order.status.in_(["pending_1c", "invoiced", "paid", "shipped", "delivered"]),
            Order.created_at >= since,
        )
    )
    return Decimal(result.scalar() or 0)
