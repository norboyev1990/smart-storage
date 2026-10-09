from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import Role, Shop, ShopMember, User, Warehouse
from app.schemas import (
    MemberIn,
    MemberOut,
    MemberUpdate,
    MyShopOut,
    ShopIn,
    ShopOut,
    WarehouseIn,
    WarehouseOut,
)
from app.security import current_member, current_user, managers, owners
from app.services import get_shop_object

router = APIRouter(tags=["shops"])


@router.get("/shops", response_model=list[MyShopOut])
def my_shops(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(ShopMember)
        .options(selectinload(ShopMember.shop))
        .where(ShopMember.user_id == user.id, ShopMember.is_active.is_(True))
    )
    return [MyShopOut(shop=ShopOut.model_validate(m.shop), role=m.role) for m in rows]


@router.post("/shops", response_model=ShopOut, status_code=201)
def create_shop(body: ShopIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Any Telegram user can register their own shop and becomes its owner."""
    shop = Shop(**body.model_dump())
    db.add(shop)
    db.flush()
    db.add(ShopMember(shop_id=shop.id, user_id=user.id, role=Role.owner))
    db.add(Warehouse(shop_id=shop.id, name="Основной склад"))
    db.commit()
    return shop


@router.get("/members", response_model=list[MemberOut])
def list_members(member: ShopMember = Depends(managers), db: Session = Depends(get_db)):
    return db.scalars(
        select(ShopMember).options(selectinload(ShopMember.user)).where(ShopMember.shop_id == member.shop_id)
    ).all()


@router.post("/members", response_model=MemberOut, status_code=201)
def add_member(body: MemberIn, member: ShopMember = Depends(owners), db: Session = Depends(get_db)):
    """Add an employee by Telegram id. The user record is created if they never opened the app."""
    user = db.scalar(select(User).where(User.telegram_id == body.telegram_id))
    if user is None:
        user = User(telegram_id=body.telegram_id, first_name=body.first_name)
        db.add(user)
        db.flush()
    new = ShopMember(shop_id=member.shop_id, user_id=user.id, role=body.role)
    db.add(new)
    try:
        db.commit()
    except IntegrityError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Already a member") from exc
    db.refresh(new)
    return new


@router.patch("/members/{member_id}", response_model=MemberOut)
def update_member(
    member_id: int, body: MemberUpdate, member: ShopMember = Depends(owners), db: Session = Depends(get_db)
):
    target = get_shop_object(db, ShopMember, member_id, member)
    if target.id == member.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot change your own membership")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(target, key, value)
    db.commit()
    return target


@router.get("/warehouses", response_model=list[WarehouseOut])
def list_warehouses(member: ShopMember = Depends(current_member), db: Session = Depends(get_db)):
    return db.scalars(select(Warehouse).where(Warehouse.shop_id == member.shop_id).order_by(Warehouse.id)).all()


@router.post("/warehouses", response_model=WarehouseOut, status_code=201)
def create_warehouse(body: WarehouseIn, member: ShopMember = Depends(managers), db: Session = Depends(get_db)):
    warehouse = Warehouse(shop_id=member.shop_id, **body.model_dump())
    db.add(warehouse)
    db.commit()
    return warehouse
