from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import Phone, PhoneStatus, Purchase, Role, Sale, ShopMember
from app.schemas import InStockRow, MoneyTotal, SoldRow, SummaryOut
from app.security import current_member
from app.services import phone_cost

router = APIRouter(prefix="/reports", tags=["reports"])

STOCK = (PhoneStatus.in_stock, PhoneStatus.reserved)


def _totals(values: dict) -> list[MoneyTotal]:
    return [MoneyTotal(currency=c, amount=a) for c, a in sorted(values.items(), key=lambda kv: kv[0].value)]


def _as_utc(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _sold_sales(db: Session, member: ShopMember, date_from, date_to, user_id):
    stmt = (
        select(Sale)
        .join(Phone)
        .options(
            selectinload(Sale.phone).selectinload(Phone.purchase),
            selectinload(Sale.phone).selectinload(Phone.expenses),
        )
        .where(Phone.shop_id == member.shop_id, Sale.is_cancelled.is_(False))
    )
    if date_from:
        stmt = stmt.where(Sale.sold_at >= date_from)
    if date_to:
        stmt = stmt.where(Sale.sold_at < date_to)
    if user_id:
        stmt = stmt.where(Sale.user_id == user_id)
    return db.scalars(stmt.order_by(Sale.sold_at.desc())).all()


def _stock_phones(db: Session, member: ShopMember, warehouse_id=None):
    stmt = (
        select(Phone)
        .options(selectinload(Phone.purchase), selectinload(Phone.expenses))
        .where(Phone.shop_id == member.shop_id, Phone.status.in_(STOCK))
    )
    if warehouse_id:
        stmt = stmt.where(Phone.warehouse_id == warehouse_id)
    return db.scalars(stmt).all()


@router.get("/summary", response_model=SummaryOut)
def summary(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    member: ShopMember = Depends(current_member),
    db: Session = Depends(get_db),
):
    show_profit = member.role != Role.seller
    stock_cost: dict = defaultdict(Decimal)
    stock = _stock_phones(db, member)
    for phone in stock:
        if cost := phone_cost(phone):
            stock_cost[cost[1]] += cost[0]

    revenue: dict = defaultdict(Decimal)
    profit: dict = defaultdict(Decimal)
    sales = _sold_sales(db, member, date_from, date_to, None)
    for sale in sales:
        revenue[sale.currency] += sale.price
        cost = phone_cost(sale.phone)
        if cost and cost[1] == sale.currency:
            profit[sale.currency] += sale.price - cost[0]

    return SummaryOut(
        in_stock_count=len(stock),
        in_stock_cost=_totals(stock_cost) if show_profit else [],
        sold_count=len(sales),
        revenue=_totals(revenue),
        profit=_totals(profit) if show_profit else None,
    )


@router.get("/sold", response_model=list[SoldRow])
def sold(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    user_id: int | None = None,
    member: ShopMember = Depends(current_member),
    db: Session = Depends(get_db),
):
    show_profit = member.role != Role.seller
    rows = []
    for sale in _sold_sales(db, member, date_from, date_to, user_id):
        row = SoldRow(
            sale_id=sale.id,
            phone_id=sale.phone_id,
            brand=sale.phone.brand,
            model=sale.phone.model,
            imei1=sale.phone.imei1,
            sold_at=sale.sold_at,
            price=sale.price,
            currency=sale.currency,
            user_id=sale.user_id,
        )
        cost = phone_cost(sale.phone)
        if show_profit and cost:
            row.cost = cost[0]
            if cost[1] == sale.currency:
                row.profit = sale.price - cost[0]
        rows.append(row)
    return rows


@router.get("/in-stock", response_model=list[InStockRow])
def in_stock(
    warehouse_id: int | None = None,
    min_days: int = 0,
    member: ShopMember = Depends(current_member),
    db: Session = Depends(get_db),
):
    show_cost = member.role != Role.seller
    now = datetime.now(timezone.utc)
    rows = []
    for phone in _stock_phones(db, member, warehouse_id):
        received = phone.purchase.purchased_at if phone.purchase else phone.created_at
        days = (now - _as_utc(received)).days
        if days < min_days:
            continue
        cost = phone_cost(phone) if show_cost else None
        rows.append(
            InStockRow(
                phone_id=phone.id,
                brand=phone.brand,
                model=phone.model,
                imei1=phone.imei1,
                warehouse_id=phone.warehouse_id,
                days_in_stock=days,
                cost=cost[0] if cost else None,
                currency=cost[1] if cost else None,
                asking_price=phone.asking_price,
                asking_currency=phone.asking_currency,
            )
        )
    return sorted(rows, key=lambda r: r.days_in_stock, reverse=True)
