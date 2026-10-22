"""Web admin panel at /admin for the service owner: every shop's data in one place.

Login and password come from ADMIN_USERNAME / ADMIN_PASSWORD in .env; with an
empty password the panel is not mounted at all. Records are never deleted from
here (history and reports depend on them): deactivate or cancel instead.
"""
import hmac

from fastapi import FastAPI
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from sqladmin.filters import BooleanFilter, ForeignKeyFilter, StaticValuesFilter
from sqladmin.i18n import I18nConfig
from starlette.requests import Request

from app.config import get_settings
from app.db import engine
from app.models import (
    Client,
    Phone,
    PhoneExpense,
    PhoneStatus,
    Purchase,
    Role,
    Sale,
    Shop,
    ShopMember,
    User,
    Warehouse,
)


class PasswordAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        settings = get_settings()
        ok = hmac.compare_digest(str(form.get("username", "")), settings.admin_username) & hmac.compare_digest(
            str(form.get("password", "")), settings.admin_password
        )
        if ok:
            request.session["admin"] = True
        return ok

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return request.session.get("admin") is True


def _values(e) -> list[tuple[str, str]]:
    return [(m.value, m.value) for m in e]


class BaseView(ModelView):
    can_delete = False
    can_export = True
    page_size = 50
    column_labels = {
        "id": "ID",
        "created_at": "Создан",
        "shop": "Магазин",
        "shop_id": "Магазин",
        "user": "Пользователь",
        "is_active": "Активен",
        "notes": "Заметки",
    }


def _shop_filter(model) -> ForeignKeyFilter:
    return ForeignKeyFilter(model.shop_id, Shop.name, foreign_model=Shop, title="Магазин")


class ShopAdmin(BaseView, model=Shop):
    name, name_plural, icon = "Магазин", "Магазины", "fa-solid fa-store"
    column_list = [Shop.id, Shop.name, Shop.default_currency, Shop.created_at]
    column_searchable_list = [Shop.name]
    column_default_sort = (Shop.id, True)
    column_labels = BaseView.column_labels | {"name": "Название", "default_currency": "Валюта"}
    form_excluded_columns = [Shop.created_at]


class UserAdmin(BaseView, model=User):
    name, name_plural, icon = "Пользователь", "Пользователи", "fa-solid fa-user"
    can_create = False  # users appear on their first Telegram login
    column_list = [User.id, User.telegram_id, User.first_name, User.last_name, User.username, User.created_at]
    column_searchable_list = [User.first_name, User.last_name, User.username, User.telegram_id]
    column_default_sort = (User.id, True)
    column_labels = BaseView.column_labels | {
        "telegram_id": "Telegram ID",
        "first_name": "Имя",
        "last_name": "Фамилия",
        "username": "Username",
        "memberships": "Магазины",
    }
    form_excluded_columns = [User.created_at, User.memberships]


class ShopMemberAdmin(BaseView, model=ShopMember):
    name, name_plural, icon = "Сотрудник", "Сотрудники", "fa-solid fa-users"
    column_list = [ShopMember.id, ShopMember.shop, ShopMember.user, ShopMember.role, ShopMember.is_active]
    column_filters = [
        _shop_filter(ShopMember),
        StaticValuesFilter(ShopMember.role, _values(Role), title="Роль"),
        BooleanFilter(ShopMember.is_active, title="Активен"),
    ]
    column_labels = BaseView.column_labels | {"role": "Роль"}
    form_columns = [ShopMember.shop, ShopMember.user, ShopMember.role, ShopMember.is_active]
    form_ajax_refs = {"user": {"fields": ("first_name", "last_name", "username"), "order_by": "id"}}


class WarehouseAdmin(BaseView, model=Warehouse):
    name, name_plural, icon = "Склад", "Склады", "fa-solid fa-warehouse"
    column_list = [Warehouse.id, Warehouse.shop, Warehouse.name, Warehouse.address, Warehouse.is_active]
    column_filters = [_shop_filter(Warehouse), BooleanFilter(Warehouse.is_active, title="Активен")]
    column_labels = BaseView.column_labels | {"name": "Название", "address": "Адрес"}
    form_columns = [Warehouse.shop, Warehouse.name, Warehouse.address, Warehouse.is_active]


class ClientAdmin(BaseView, model=Client):
    name, name_plural, icon = "Клиент", "Клиенты", "fa-solid fa-address-book"
    column_list = [Client.id, Client.shop_id, Client.full_name, Client.phone_number, Client.document, Client.created_at]
    column_searchable_list = [Client.full_name, Client.phone_number, Client.document]
    column_filters = [_shop_filter(Client)]
    column_default_sort = (Client.id, True)
    column_labels = BaseView.column_labels | {"full_name": "ФИО", "phone_number": "Телефон", "document": "Документ"}
    form_excluded_columns = [Client.created_at]


class PhoneAdmin(BaseView, model=Phone):
    name, name_plural, icon = "Телефон", "Телефоны", "fa-solid fa-mobile-screen"
    column_list = [
        Phone.id,
        Phone.shop_id,
        Phone.brand,
        Phone.model,
        Phone.storage_gb,
        Phone.imei1,
        Phone.condition,
        Phone.status,
        Phone.asking_price,
        Phone.asking_currency,
        Phone.created_at,
    ]
    column_searchable_list = [Phone.brand, Phone.model, Phone.imei1, Phone.imei2, Phone.serial_number]
    column_filters = [
        _shop_filter(Phone),
        StaticValuesFilter(Phone.status, _values(PhoneStatus), title="Статус"),
    ]
    column_default_sort = (Phone.id, True)
    column_labels = BaseView.column_labels | {
        "warehouse": "Склад",
        "brand": "Бренд",
        "model": "Модель",
        "storage_gb": "Память, ГБ",
        "ram_gb": "ОЗУ, ГБ",
        "color": "Цвет",
        "imei1": "IMEI 1",
        "imei2": "IMEI 2",
        "serial_number": "Серийный номер",
        "condition": "Состояние",
        "battery_health": "Батарея, %",
        "kit": "Комплект",
        "status": "Статус",
        "asking_price": "Цена продажи",
        "asking_currency": "Валюта",
        "updated_at": "Изменён",
        "purchase": "Покупка",
        "sales": "Продажи",
        "expenses": "Расходы",
    }
    form_excluded_columns = [Phone.created_at, Phone.updated_at, Phone.purchase, Phone.sales, Phone.expenses]


class PurchaseAdmin(BaseView, model=Purchase):
    name, name_plural, icon = "Покупка", "Покупки", "fa-solid fa-cart-arrow-down"
    can_create = False  # a purchase is created together with its phone in the Mini App
    column_list = [
        Purchase.id,
        Purchase.phone,
        Purchase.client,
        Purchase.price,
        Purchase.currency,
        Purchase.payment_method,
        Purchase.purchased_at,
    ]
    column_default_sort = (Purchase.purchased_at, True)
    column_labels = BaseView.column_labels | {
        "phone": "Телефон",
        "client": "Продавец",
        "user_id": "Принял",
        "price": "Цена",
        "currency": "Валюта",
        "payment_method": "Оплата",
        "purchased_at": "Дата",
    }
    form_excluded_columns = [Purchase.created_at, Purchase.phone]


class SaleAdmin(BaseView, model=Sale):
    name, name_plural, icon = "Продажа", "Продажи", "fa-solid fa-cash-register"
    can_create = False  # selling also changes the phone status: use the Mini App
    column_list = [
        Sale.id,
        Sale.phone,
        Sale.client,
        Sale.price,
        Sale.currency,
        Sale.payment_method,
        Sale.sold_at,
        Sale.is_cancelled,
    ]
    column_filters = [BooleanFilter(Sale.is_cancelled, title="Отменена")]
    column_default_sort = (Sale.sold_at, True)
    column_labels = BaseView.column_labels | {
        "phone": "Телефон",
        "client": "Покупатель",
        "user_id": "Продал",
        "price": "Цена",
        "currency": "Валюта",
        "payment_method": "Оплата",
        "warranty_days": "Гарантия, дней",
        "sold_at": "Дата",
        "is_cancelled": "Отменена",
        "cancelled_reason": "Причина отмены",
    }
    form_excluded_columns = [Sale.created_at, Sale.phone]


class PhoneExpenseAdmin(BaseView, model=PhoneExpense):
    name, name_plural, icon = "Расход", "Расходы", "fa-solid fa-screwdriver-wrench"
    column_list = [
        PhoneExpense.id,
        PhoneExpense.phone,
        PhoneExpense.amount,
        PhoneExpense.currency,
        PhoneExpense.description,
        PhoneExpense.created_at,
    ]
    column_default_sort = (PhoneExpense.id, True)
    column_labels = BaseView.column_labels | {
        "phone": "Телефон",
        "user_id": "Добавил",
        "amount": "Сумма",
        "currency": "Валюта",
        "description": "Описание",
    }
    can_create = False
    form_excluded_columns = [PhoneExpense.created_at, PhoneExpense.phone]


VIEWS = [
    ShopAdmin,
    ShopMemberAdmin,
    WarehouseAdmin,
    UserAdmin,
    PhoneAdmin,
    PurchaseAdmin,
    SaleAdmin,
    PhoneExpenseAdmin,
    ClientAdmin,
]


def mount_admin(app: FastAPI) -> Admin | None:
    settings = get_settings()
    if not settings.admin_password:
        return None
    admin = Admin(
        app,
        engine,
        title="Smart Storage",
        authentication_backend=PasswordAuth(secret_key=settings.jwt_secret),
        i18n_config=I18nConfig(default_locale="ru"),
    )
    for view in VIEWS:
        admin.add_view(view)
    return admin
