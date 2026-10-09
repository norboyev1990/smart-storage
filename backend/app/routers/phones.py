from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import Phone, PhoneExpense, PhoneStatus, Purchase, Sale, ShopMember
from app.schemas import (
    ExpenseIn,
    ExpenseOut,
    Page,
    PhoneCreate,
    PhoneDetail,
    PhoneOut,
    PhoneUpdate,
    SaleCancelIn,
    SaleIn,
    SaleOut,
)
from app.security import current_member, managers
from app.services import check_warehouse, get_shop_object, resolve_client

router = APIRouter(tags=["phones"])

SELLABLE = (PhoneStatus.in_stock, PhoneStatus.reserved)


def _load_phone(db: Session, phone_id: int, member: ShopMember, lock: bool = False) -> Phone:
    stmt = select(Phone).where(Phone.id == phone_id, Phone.shop_id == member.shop_id)
    if lock:
        stmt = stmt.with_for_update()
    phone = db.scalar(
        stmt.options(
            selectinload(Phone.purchase).selectinload(Purchase.client),
            selectinload(Phone.sales).selectinload(Sale.client),
            selectinload(Phone.expenses),
        )
    )
    if phone is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Phone not found")
    return phone


@router.get("/phones", response_model=Page[PhoneOut])
def list_phones(
    status_: PhoneStatus | None = Query(None, alias="status"),
    warehouse_id: int | None = None,
    brand: str | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
    member: ShopMember = Depends(current_member),
    db: Session = Depends(get_db),
):
    stmt = select(Phone).where(Phone.shop_id == member.shop_id)
    if status_:
        stmt = stmt.where(Phone.status == status_)
    if warehouse_id:
        stmt = stmt.where(Phone.warehouse_id == warehouse_id)
    if brand:
        stmt = stmt.where(Phone.brand.ilike(brand))
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(Phone.model.ilike(like), Phone.brand.ilike(like), Phone.imei1.like(like), Phone.imei2.like(like))
        )
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(Phone.created_at.desc(), Phone.id.desc()).limit(limit).offset(offset)).all()
    return Page(items=items, total=total)


@router.post("/phones", response_model=PhoneDetail, status_code=201)
def create_phone(body: PhoneCreate, member: ShopMember = Depends(current_member), db: Session = Depends(get_db)):
    """Accept a phone bought from a client: the phone and its purchase are created together."""
    check_warehouse(db, member, body.warehouse_id)
    duplicate = db.scalar(
        select(Phone.id).where(
            Phone.shop_id == member.shop_id, Phone.imei1 == body.imei1, Phone.status.in_(SELLABLE)
        )
    )
    if duplicate:
        raise HTTPException(status.HTTP_409_CONFLICT, "A phone with this IMEI is already in stock")

    data = body.model_dump(exclude={"purchase"})
    phone = Phone(shop_id=member.shop_id, **data)
    db.add(phone)
    db.flush()

    p = body.purchase
    client = resolve_client(db, member, p.client_id, p.client)
    db.add(
        Purchase(
            phone_id=phone.id,
            client_id=client.id if client else None,
            user_id=member.user_id,
            price=p.price,
            currency=p.currency,
            payment_method=p.payment_method,
            purchased_at=p.purchased_at or datetime.now(timezone.utc),
            notes=p.notes,
        )
    )
    db.commit()
    return _load_phone(db, phone.id, member)


@router.get("/phones/{phone_id}", response_model=PhoneDetail)
def get_phone(phone_id: int, member: ShopMember = Depends(current_member), db: Session = Depends(get_db)):
    return _load_phone(db, phone_id, member)


@router.patch("/phones/{phone_id}", response_model=PhoneDetail)
def update_phone(
    phone_id: int, body: PhoneUpdate, member: ShopMember = Depends(current_member), db: Session = Depends(get_db)
):
    phone = _load_phone(db, phone_id, member)
    changes = body.model_dump(exclude_unset=True)
    if "status" in changes and PhoneStatus.sold in (changes["status"], phone.status):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Use /sell or cancel the sale to change the sold status")
    if "warehouse_id" in changes:
        check_warehouse(db, member, changes["warehouse_id"])
    for key, value in changes.items():
        setattr(phone, key, value)
    db.commit()
    return _load_phone(db, phone_id, member)


@router.post("/phones/{phone_id}/expenses", response_model=ExpenseOut, status_code=201)
def add_expense(
    phone_id: int, body: ExpenseIn, member: ShopMember = Depends(current_member), db: Session = Depends(get_db)
):
    phone = _load_phone(db, phone_id, member)
    expense = PhoneExpense(phone_id=phone.id, user_id=member.user_id, **body.model_dump())
    db.add(expense)
    db.commit()
    return expense


@router.post("/phones/{phone_id}/sell", response_model=SaleOut, status_code=201)
def sell_phone(
    phone_id: int, body: SaleIn, member: ShopMember = Depends(current_member), db: Session = Depends(get_db)
):
    phone = _load_phone(db, phone_id, member, lock=True)
    if phone.status not in SELLABLE:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Phone cannot be sold, status is {phone.status.value}")
    client = resolve_client(db, member, body.client_id, body.client)
    sale = Sale(
        phone_id=phone.id,
        client_id=client.id if client else None,
        user_id=member.user_id,
        **body.model_dump(exclude={"client_id", "client", "sold_at"}),
        sold_at=body.sold_at or datetime.now(timezone.utc),
    )
    phone.status = PhoneStatus.sold
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale


@router.post("/sales/{sale_id}/cancel", response_model=SaleOut)
def cancel_sale(
    sale_id: int, body: SaleCancelIn, member: ShopMember = Depends(managers), db: Session = Depends(get_db)
):
    """Return: the sale is kept for history, the phone goes back to stock."""
    sale = db.get(Sale, sale_id)
    if sale is None or sale.phone.shop_id != member.shop_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sale not found")
    if sale.is_cancelled:
        raise HTTPException(status.HTTP_409_CONFLICT, "Sale is already cancelled")
    sale.is_cancelled = True
    sale.cancelled_reason = body.reason
    sale.phone.status = PhoneStatus.in_stock
    db.commit()
    return sale
