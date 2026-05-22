"""
ORM-модели с поддержкой:
  • регистрации по ИНН (one_c_id, client_tier)
  • лимитов по уровню клиента (TierLimit)
  • счёта и договора из 1С (Order.invoice_url, contract_url)
  • вариантов фасовки (ProductVariant — 50/100 опр.)
  • брендов (Product.brand — SNIBE, DYMIND, BD...)
  • товаров "по запросу" (ProductVariant.is_orderable=False)
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    String, Integer, Numeric, Boolean, DateTime, Text,
    ForeignKey, JSON, BigInteger, UniqueConstraint, Index,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def now() -> datetime:
    return datetime.now(timezone.utc)


def uid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


# ─── Organizations ────────────────────────────────────────────────────────────

class Organization(Base):
    __tablename__ = "organizations"

    id:           Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    inn:          Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name:         Mapped[str] = mapped_column(String(255))
    type:         Mapped[str] = mapped_column(String(50))
    phone:        Mapped[str] = mapped_column(String(20), default="")
    address:      Mapped[str] = mapped_column(Text, default="")

    one_c_id:     Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    client_tier:  Mapped[str] = mapped_column(String(20), default="standard")

    status:       Mapped[str] = mapped_column(String(20), default="pending")
    created_at:   Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at:   Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    users:  Mapped[list["User"]]  = relationship(back_populates="organization")
    orders: Mapped[list["Order"]] = relationship(back_populates="organization")


# ─── Users ────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id:          Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    first_name:  Mapped[str] = mapped_column(String(100), default="")
    last_name:   Mapped[str] = mapped_column(String(100), default="")
    role:        Mapped[str] = mapped_column(String(20), default="client")
    org_id:      Mapped[str | None] = mapped_column(ForeignKey("organizations.id"), nullable=True)
    status:      Mapped[str] = mapped_column(String(20), default="pending")
    # "ru" | "uz" — set at registration, updated by language switcher.
    # NOTE: existing databases need: ALTER TABLE users ADD COLUMN language VARCHAR(5) DEFAULT 'ru';
    language:    Mapped[str] = mapped_column(String(5), default="ru", server_default="ru")
    created_at:  Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    organization: Mapped["Organization | None"] = relationship(back_populates="users")
    orders:       Mapped[list["Order"]] = relationship(back_populates="user")
    cart_items:   Mapped[list["CartItem"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


# ─── Categories ───────────────────────────────────────────────────────────────

class Category(Base):
    """
    Иерархия категорий по направлениям диагностики:
      ИХЛА → Щитовидная панель → товары
      Биохимия → Липиды → товары
      и т.д.
    """
    __tablename__ = "categories"

    id:         Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name:       Mapped[str] = mapped_column(String(200))
    parent_id:  Mapped[str | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    one_c_id:   Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


# ─── Brands ───────────────────────────────────────────────────────────────────

class Brand(Base):
    """Производители: SNIBE, DYMIND, Werfen, BD, URIT, Lifotronic, RANDOX."""
    __tablename__ = "brands"

    id:         Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    code:       Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name:       Mapped[str] = mapped_column(String(200))
    logo_url:   Mapped[str] = mapped_column(String(500), default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


# ─── Products ─────────────────────────────────────────────────────────────────

class Product(Base):
    """
    Товар — это реагент/тест/расходник.
    Цены и фасовки хранятся в ProductVariant (один товар = несколько вариантов).
    """
    __tablename__ = "products"

    id:               Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    one_c_id:         Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    name:             Mapped[str] = mapped_column(String(255))
    short_name:       Mapped[str] = mapped_column(String(100), default="")   # TSH, FT4, ALT
    description:      Mapped[str] = mapped_column(Text, default="")
    category_id:      Mapped[str | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    brand_id:         Mapped[str | None] = mapped_column(ForeignKey("brands.id"), nullable=True)
    image_url:        Mapped[str] = mapped_column(String(500), default="")
    is_active:        Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at:       Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    variants:  Mapped[list["ProductVariant"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )


class ProductVariant(Base):
    """
    Конкретная фасовка товара с ценой.
    Примеры:
      TSH: "50 определений" — 790 720 сум
      TSH: "100 определений" — 1 048 320 сум
      Промывочный концентрат: "1x714 мл" — 283 360 сум

    is_orderable=False — товар "По запросу", показывается без кнопки заказа.
    """
    __tablename__ = "product_variants"

    id:               Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    product_id:       Mapped[str] = mapped_column(ForeignKey("products.id"))
    one_c_id:         Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    sku:              Mapped[str] = mapped_column(String(100), unique=True, index=True)
    pack_size:        Mapped[str] = mapped_column(String(100))   # "50 опред." / "100 опред." / "2x230 мл"
    price:            Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    is_orderable:     Mapped[bool] = mapped_column(Boolean, default=True)
    stock_qty:        Mapped[int] = mapped_column(Integer, default=0)
    unit:             Mapped[str] = mapped_column(String(20), default="упак")
    sort_order:       Mapped[int] = mapped_column(Integer, default=0)
    stock_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    product: Mapped["Product"] = relationship(back_populates="variants")


# ─── Tier Limits ──────────────────────────────────────────────────────────────

class TierLimit(Base):
    __tablename__ = "tier_limits"
    __table_args__ = (
        UniqueConstraint("tier", "category_id", name="uq_tier_category"),
        Index("idx_tier_limits_lookup", "tier", "category_id"),
    )

    id:                     Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    tier:                   Mapped[str] = mapped_column(String(20))
    category_id:            Mapped[str | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    max_qty_per_order:      Mapped[int] = mapped_column(Integer, default=999_999)
    max_qty_per_month:      Mapped[int] = mapped_column(Integer, default=999_999)
    max_amount_per_month:   Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("99999999"))


# ─── Cart ─────────────────────────────────────────────────────────────────────

class CartItem(Base):
    """Корзина теперь хранит variant_id, а не product_id."""
    __tablename__ = "cart_items"
    __table_args__ = (UniqueConstraint("user_id", "variant_id", name="uq_cart_user_variant"),)

    id:         Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id:    Mapped[str] = mapped_column(ForeignKey("users.id"))
    variant_id: Mapped[str] = mapped_column(ForeignKey("product_variants.id"))
    quantity:   Mapped[int] = mapped_column(Integer, default=1)
    added_at:   Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    user:    Mapped["User"]           = relationship(back_populates="cart_items")
    variant: Mapped["ProductVariant"] = relationship()


# ─── Orders ───────────────────────────────────────────────────────────────────

class Order(Base):
    __tablename__ = "orders"

    id:              Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id:         Mapped[str] = mapped_column(ForeignKey("users.id"))
    org_id:          Mapped[str] = mapped_column(ForeignKey("organizations.id"))

    status:          Mapped[str] = mapped_column(String(30), default="draft")
    total_amount:    Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    comment:         Mapped[str] = mapped_column(Text, default="")

    one_c_id:        Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    invoice_number:  Mapped[str | None] = mapped_column(String(50), nullable=True)
    invoice_url:     Mapped[str | None] = mapped_column(String(500), nullable=True)
    contract_url:    Mapped[str | None] = mapped_column(String(500), nullable=True)
    synced_to_1c:    Mapped[bool] = mapped_column(Boolean, default=False)
    synced_at:       Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    paid_at:         Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payment_method:  Mapped[str] = mapped_column(String(30), default="bank_transfer")

    created_at:      Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at:      Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    user:         Mapped["User"]         = relationship(back_populates="orders")
    organization: Mapped["Organization"] = relationship(back_populates="orders")
    items:        Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    events:       Mapped[list["OrderEvent"]] = relationship(back_populates="order")


class OrderItem(Base):
    """В заказе хранится variant_id, плюс снимок данных на момент заказа."""
    __tablename__ = "order_items"

    id:           Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    order_id:     Mapped[str] = mapped_column(ForeignKey("orders.id"))
    variant_id:   Mapped[str] = mapped_column(ForeignKey("product_variants.id"))
    # Снимок на момент заказа (на случай если потом изменится в каталоге)
    product_name: Mapped[str] = mapped_column(String(255))
    pack_size:    Mapped[str] = mapped_column(String(100))
    sku:          Mapped[str] = mapped_column(String(100))
    quantity:     Mapped[int] = mapped_column(Integer)
    unit_price:   Mapped[Decimal] = mapped_column(Numeric(14, 2))
    subtotal:     Mapped[Decimal] = mapped_column(Numeric(14, 2))

    order:   Mapped["Order"]          = relationship(back_populates="items")
    variant: Mapped["ProductVariant"] = relationship()


# ─── Order Events ─────────────────────────────────────────────────────────────

class OrderEvent(Base):
    __tablename__ = "order_events"

    id:         Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    order_id:   Mapped[str] = mapped_column(ForeignKey("orders.id"))
    event_type: Mapped[str] = mapped_column(String(50))
    payload:    Mapped[dict] = mapped_column(JSON, default=dict)
    notified:   Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    order: Mapped["Order"] = relationship(back_populates="events")


# ─── Sync Log ─────────────────────────────────────────────────────────────────

class SyncLog(Base):
    __tablename__ = "sync_logs"

    id:          Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    entity:      Mapped[str] = mapped_column(String(50))
    status:      Mapped[str] = mapped_column(String(20))
    started_at:  Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[int] = mapped_column(Integer)
    details:     Mapped[dict] = mapped_column(JSON, default=dict)
