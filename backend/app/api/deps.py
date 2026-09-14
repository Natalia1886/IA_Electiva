from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import roles_for
from app.core.security import decode_access_token
from app.database import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
DbDep = Annotated[AsyncSession, Depends(get_db)]

# These dependencies are the authentication / authorization middleware of the
# API: get_current_user verifies the caller's identity (JWT + active user) and
# the require_* factories verify role / resource permissions declaratively.


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DbDep,
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar la sesión",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        username: str = payload.get("sub", "")
        if not username:
            raise credentials_error
    except InvalidTokenError:
        raise credentials_error

    result = await db.execute(select(User).where(User.username == username, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_error
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*roles: str):
    """Declarative role gate, e.g. ``Depends(require_role("admin"))``."""
    def dependency(user: CurrentUser) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para realizar esta acción",
            )
        return user

    return dependency


require_roles = require_role


def require_permission(permission: str):
    """Declarative resource-authorization gate.

    Verifies that the caller's role is allowed to exercise ``permission`` as
    defined in ``app.core.permissions.PERMISSIONS``, e.g.
    ``Depends(require_permission("inventory:view:alerts"))``.
    """
    def dependency(user: CurrentUser) -> User:
        if user.role not in roles_for(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para realizar esta acción",
            )
        return user

    return dependency


AdminUser = Annotated[User, Depends(require_role("admin"))]
AnyUser = Annotated[User, Depends(require_role("admin", "salesperson"))]