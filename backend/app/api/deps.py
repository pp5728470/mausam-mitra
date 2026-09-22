from collections.abc import AsyncGenerator
from typing import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.enums import Role
from app.db.session import get_db
from app.models.user import User
from app.schemas.token import TokenPayload


reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login"
)


async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> User:
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        token_data = TokenPayload(**payload)
    except (jwt.PyJWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    user = await db.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


async def get_current_user_optional(
    db: AsyncSession = Depends(get_db),
    token: str | None = Depends(OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False))
) -> User | None:
    if not token:
        return None
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        token_data = TokenPayload(**payload)
    except (jwt.PyJWTError, ValidationError):
        return None
    user = await db.get(User, token_data.sub)
    if not user or not user.is_active:
        return None
    return user


def require_roles(*roles: Role) -> Callable:
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles and current_user.role != Role.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        return current_user
    return role_checker


def require_role(role: Role) -> Callable:
    return require_roles(role)
