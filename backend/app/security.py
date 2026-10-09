from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import Role, ShopMember, User

bearer = HTTPBearer(auto_error=False)


def create_token(user_id: int) -> str:
    settings = get_settings()
    expires = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_ttl_hours)
    return jwt.encode({"sub": str(user_id), "exp": expires}, settings.jwt_secret, algorithm="HS256")


def current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        payload = jwt.decode(creds.credentials, get_settings().jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token") from exc
    user = db.get(User, int(payload["sub"]))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user


def current_member(
    x_shop_id: int = Header(..., description="Active shop"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> ShopMember:
    """The caller's membership in the shop chosen by the X-Shop-Id header."""
    member = db.scalar(
        select(ShopMember).where(
            ShopMember.shop_id == x_shop_id,
            ShopMember.user_id == user.id,
            ShopMember.is_active.is_(True),
        )
    )
    if member is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No access to this shop")
    return member


def require_roles(*roles: Role):
    def dep(member: ShopMember = Depends(current_member)) -> ShopMember:
        if member.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not enough rights")
        return member

    return dep


managers = require_roles(Role.owner, Role.manager)
owners = require_roles(Role.owner)
