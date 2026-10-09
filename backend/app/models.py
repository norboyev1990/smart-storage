"""Data model.

Multi-tenant: every shop is isolated. A user (Telegram account) can be a member
of several shops with a role in each. A shop has one or more warehouses; phones
live in a warehouse. Money is stored as Numeric with an explicit currency (UZS/USD).
"""
import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

Money = Numeric(14, 2)


class Currency(str, enum.Enum):
    UZS = "UZS"
    USD = "USD"


class Role(str, enum.Enum):
    owner = "owner"      # everything, incl. members and profit
    manager = "manager"  # everything except members
    seller = "seller"    # purchases and sales, no profit in reports


class PhoneStatus(str, enum.Enum):
    in_stock = "in_stock"
    reserved = "reserved"
    sold = "sold"
    returned = "returned"
    written_off = "written_off"


class Condition(str, enum.Enum):
    new = "new"
    excellent = "excellent"
    good = "good"
    fair = "fair"
    broken = "broken"


class PaymentMethod(str, enum.Enum):
    cash = "cash"
    card = "card"
    transfer = "transfer"


def _enum(e: type[enum.Enum]) -> Enum:
    return Enum(e, native_enum=False, length=20)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(128), default="")
    last_name: Mapped[str | None] = mapped_column(String(128))
    username: Mapped[str | None] = mapped_column(String(64))

    memberships: Mapped[list["ShopMember"]] = relationship(back_populates="user")


class Shop(TimestampMixin, Base):
    __tablename__ = "shops"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    default_currency: Mapped[Currency] = mapped_column(_enum(Currency), default=Currency.UZS)

    members: Mapped[list["ShopMember"]] = relationship(back_populates="shop")
    warehouses: Mapped[list["Warehouse"]] = relationship(back_populates="shop")


class ShopMember(TimestampMixin, Base):
    __tablename__ = "shop_members"
    __table_args__ = (UniqueConstraint("shop_id", "user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    shop_id: Mapped[int] = mapped_column(ForeignKey("shops.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[Role] = mapped_column(_enum(Role))
    is_active: Mapped[bool] = mapped_column(default=True)

    shop: Mapped[Shop] = relationship(back_populates="members")
    user: Mapped[User] = relationship(back_populates="memberships")


class Warehouse(TimestampMixin, Base):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(primary_key=True)
    shop_id: Mapped[int] = mapped_column(ForeignKey("shops.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(128))
    address: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)

    shop: Mapped[Shop] = relationship(back_populates="warehouses")


class Client(TimestampMixin, Base):
    """A person who sells a phone to the shop or buys one from it."""

    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    shop_id: Mapped[int] = mapped_column(ForeignKey("shops.id", ondelete="CASCADE"), index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    phone_number: Mapped[str | None] = mapped_column(String(32), index=True)
    document: Mapped[str | None] = mapped_column(String(64))  # passport / ID, optional
    notes: Mapped[str | None] = mapped_column(Text)


class Phone(TimestampMixin, Base):
    __tablename__ = "phones"
    __table_args__ = (UniqueConstraint("shop_id", "imei1"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    shop_id: Mapped[int] = mapped_column(ForeignKey("shops.id", ondelete="CASCADE"), index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), index=True)
    brand: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(128))
    storage_gb: Mapped[int | None]
    ram_gb: Mapped[int | None]
    color: Mapped[str | None] = mapped_column(String(64))
    imei1: Mapped[str] = mapped_column(String(20), index=True)
    imei2: Mapped[str | None] = mapped_column(String(20))
    serial_number: Mapped[str | None] = mapped_column(String(64))
    condition: Mapped[Condition] = mapped_column(_enum(Condition), default=Condition.good)
    battery_health: Mapped[int | None]
    kit: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[PhoneStatus] = mapped_column(_enum(PhoneStatus), default=PhoneStatus.in_stock, index=True)
    asking_price: Mapped[Decimal | None] = mapped_column(Money)
    asking_currency: Mapped[Currency | None] = mapped_column(_enum(Currency))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    warehouse: Mapped[Warehouse] = relationship()
    purchase: Mapped["Purchase | None"] = relationship(back_populates="phone", uselist=False)
    sales: Mapped[list["Sale"]] = relationship(back_populates="phone", order_by="Sale.sold_at")
    expenses: Mapped[list["PhoneExpense"]] = relationship(back_populates="phone")


class Purchase(TimestampMixin, Base):
    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(primary_key=True)
    phone_id: Mapped[int] = mapped_column(ForeignKey("phones.id", ondelete="CASCADE"), unique=True)
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    price: Mapped[Decimal] = mapped_column(Money)
    currency: Mapped[Currency] = mapped_column(_enum(Currency))
    payment_method: Mapped[PaymentMethod] = mapped_column(_enum(PaymentMethod), default=PaymentMethod.cash)
    purchased_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    notes: Mapped[str | None] = mapped_column(Text)

    phone: Mapped[Phone] = relationship(back_populates="purchase")
    client: Mapped[Client | None] = relationship()


class Sale(TimestampMixin, Base):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(primary_key=True)
    phone_id: Mapped[int] = mapped_column(ForeignKey("phones.id", ondelete="CASCADE"), index=True)
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    price: Mapped[Decimal] = mapped_column(Money)
    currency: Mapped[Currency] = mapped_column(_enum(Currency))
    payment_method: Mapped[PaymentMethod] = mapped_column(_enum(PaymentMethod), default=PaymentMethod.cash)
    warranty_days: Mapped[int] = mapped_column(default=0)
    sold_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    is_cancelled: Mapped[bool] = mapped_column(default=False)
    cancelled_reason: Mapped[str | None] = mapped_column(Text)

    phone: Mapped[Phone] = relationship(back_populates="sales")
    client: Mapped[Client | None] = relationship()


class PhoneExpense(TimestampMixin, Base):
    """Repair, parts, cleaning: added to the phone's cost."""

    __tablename__ = "phone_expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    phone_id: Mapped[int] = mapped_column(ForeignKey("phones.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[Decimal] = mapped_column(Money)
    currency: Mapped[Currency] = mapped_column(_enum(Currency))
    description: Mapped[str] = mapped_column(String(255))

    phone: Mapped[Phone] = relationship(back_populates="expenses")
