from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Client, Currency, Phone, ShopMember, Warehouse
from app.schemas import ClientIn


def phone_cost(phone: Phone) -> tuple[Decimal, Currency] | None:
    """Purchase price plus expenses. None if there is no purchase or currencies are mixed."""
    if phone.purchase is None:
        return None
    currency = phone.purchase.currency
    if any(e.currency != currency for e in phone.expenses):
        return None
    return phone.purchase.price + sum((e.amount for e in phone.expenses), Decimal(0)), currency


def get_shop_object(db: Session, model, obj_id: int, member: ShopMember):
    obj = db.get(model, obj_id)
    if obj is None or obj.shop_id != member.shop_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{model.__name__} not found")
    return obj


def resolve_client(
    db: Session, member: ShopMember, client_id: int | None, client: ClientIn | None
) -> Client | None:
    if client_id is not None:
        return get_shop_object(db, Client, client_id, member)
    if client is not None:
        new = Client(shop_id=member.shop_id, **client.model_dump())
        db.add(new)
        db.flush()
        return new
    return None


def check_warehouse(db: Session, member: ShopMember, warehouse_id: int) -> Warehouse:
    warehouse = get_shop_object(db, Warehouse, warehouse_id, member)
    if not warehouse.is_active:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Warehouse is inactive")
    return warehouse
