from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Client, ShopMember
from app.schemas import ClientIn, ClientOut, Page
from app.security import current_member
from app.services import get_shop_object

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_model=Page[ClientOut])
def list_clients(
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
    member: ShopMember = Depends(current_member),
    db: Session = Depends(get_db),
):
    stmt = select(Client).where(Client.shop_id == member.shop_id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Client.full_name.ilike(like), Client.phone_number.ilike(like)))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(Client.full_name).limit(limit).offset(offset)).all()
    return Page(items=items, total=total)


@router.post("", response_model=ClientOut, status_code=201)
def create_client(body: ClientIn, member: ShopMember = Depends(current_member), db: Session = Depends(get_db)):
    client = Client(shop_id=member.shop_id, **body.model_dump())
    db.add(client)
    db.commit()
    return client


@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: int, member: ShopMember = Depends(current_member), db: Session = Depends(get_db)):
    return get_shop_object(db, Client, client_id, member)


@router.patch("/{client_id}", response_model=ClientOut)
def update_client(
    client_id: int, body: ClientIn, member: ShopMember = Depends(current_member), db: Session = Depends(get_db)
):
    client = get_shop_object(db, Client, client_id, member)
    for key, value in body.model_dump().items():
        setattr(client, key, value)
    db.commit()
    return client
