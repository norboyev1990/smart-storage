from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models import Condition, Currency, PaymentMethod, PhoneStatus, Role


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TelegramAuthIn(BaseModel):
    init_data: str


class UserOut(ORM):
    id: int
    telegram_id: int
    first_name: str
    last_name: str | None
    username: str | None


class TokenOut(BaseModel):
    access_token: str
    user: UserOut


class ShopIn(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    default_currency: Currency = Currency.UZS


class ShopOut(ORM):
    id: int
    name: str
    default_currency: Currency


class MyShopOut(BaseModel):
    shop: ShopOut
    role: Role


class MemberIn(BaseModel):
    telegram_id: int
    role: Role = Role.seller
    first_name: str = ""


class MemberUpdate(BaseModel):
    role: Role | None = None
    is_active: bool | None = None


class MemberOut(ORM):
    id: int
    role: Role
    is_active: bool
    user: UserOut


class WarehouseIn(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    address: str | None = None


class WarehouseOut(ORM):
    id: int
    name: str
    address: str | None
    is_active: bool


class ClientIn(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    phone_number: str | None = None
    document: str | None = None
    notes: str | None = None


class ClientOut(ORM):
    id: int
    full_name: str
    phone_number: str | None
    document: str | None
    notes: str | None
    created_at: datetime


class PhoneBase(BaseModel):
    brand: str = Field(min_length=1, max_length=64)
    model: str = Field(min_length=1, max_length=128)
    storage_gb: int | None = None
    ram_gb: int | None = None
    color: str | None = None
    imei1: str = Field(min_length=8, max_length=20)
    imei2: str | None = None
    serial_number: str | None = None
    condition: Condition = Condition.good
    battery_health: int | None = Field(default=None, ge=0, le=100)
    kit: str | None = None
    notes: str | None = None
    asking_price: Decimal | None = Field(default=None, ge=0)
    asking_currency: Currency | None = None


class PurchaseIn(BaseModel):
    client_id: int | None = None
    client: ClientIn | None = None  # create a new client inline
    price: Decimal = Field(ge=0)
    currency: Currency
    payment_method: PaymentMethod = PaymentMethod.cash
    purchased_at: datetime | None = None
    notes: str | None = None


class PhoneCreate(PhoneBase):
    warehouse_id: int
    purchase: PurchaseIn


class PhoneUpdate(BaseModel):
    warehouse_id: int | None = None
    brand: str | None = None
    model: str | None = None
    storage_gb: int | None = None
    ram_gb: int | None = None
    color: str | None = None
    imei2: str | None = None
    serial_number: str | None = None
    condition: Condition | None = None
    battery_health: int | None = Field(default=None, ge=0, le=100)
    kit: str | None = None
    notes: str | None = None
    status: PhoneStatus | None = None
    asking_price: Decimal | None = Field(default=None, ge=0)
    asking_currency: Currency | None = None


class PurchaseOut(ORM):
    id: int
    client: ClientOut | None
    user_id: int
    price: Decimal
    currency: Currency
    payment_method: PaymentMethod
    purchased_at: datetime
    notes: str | None


class SaleIn(BaseModel):
    client_id: int | None = None
    client: ClientIn | None = None
    price: Decimal = Field(ge=0)
    currency: Currency
    payment_method: PaymentMethod = PaymentMethod.cash
    warranty_days: int = Field(default=0, ge=0)
    sold_at: datetime | None = None
    notes: str | None = None


class SaleCancelIn(BaseModel):
    reason: str = Field(min_length=1)


class SaleOut(ORM):
    id: int
    phone_id: int
    client: ClientOut | None
    user_id: int
    price: Decimal
    currency: Currency
    payment_method: PaymentMethod
    warranty_days: int
    sold_at: datetime
    notes: str | None
    is_cancelled: bool
    cancelled_reason: str | None


class ExpenseIn(BaseModel):
    amount: Decimal = Field(gt=0)
    currency: Currency
    description: str = Field(min_length=1, max_length=255)


class ExpenseOut(ORM):
    id: int
    amount: Decimal
    currency: Currency
    description: str
    user_id: int
    created_at: datetime


class PhoneOut(PhoneBase, ORM):
    id: int
    warehouse_id: int
    status: PhoneStatus
    created_at: datetime


class PhoneDetail(PhoneOut):
    purchase: PurchaseOut | None
    sales: list[SaleOut]
    expenses: list[ExpenseOut]


class Page[T](BaseModel):
    items: list[T]
    total: int


class MoneyTotal(BaseModel):
    currency: Currency
    amount: Decimal


class SummaryOut(BaseModel):
    in_stock_count: int
    in_stock_cost: list[MoneyTotal]
    sold_count: int
    revenue: list[MoneyTotal]
    profit: list[MoneyTotal] | None  # hidden for sellers


class SoldRow(BaseModel):
    sale_id: int
    phone_id: int
    brand: str
    model: str
    imei1: str
    sold_at: datetime
    price: Decimal
    currency: Currency
    cost: Decimal | None = None
    profit: Decimal | None = None
    user_id: int


class InStockRow(BaseModel):
    phone_id: int
    brand: str
    model: str
    imei1: str
    warehouse_id: int
    days_in_stock: int
    cost: Decimal | None = None
    currency: Currency | None = None
    asking_price: Decimal | None
    asking_currency: Currency | None
