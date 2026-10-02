"""Rutas de autenticación y sesiones de usuario (RF01, RF02, HU01)."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from core.database.connection import get_db
from core.database.models import User
from core.security.auth import verify_password, create_access_token
from core.security.permissions import ROLE_PERMISSIONS
from interfaces.api.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Autenticación"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    full_name: str
    role: str
    permissions: list


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Inicio de sesión con validación de credenciales cifradas y retorno de token con rol (HU01)."""
    user = db.query(User).filter_by(username=req.username.strip()).first()

    # Mensaje genérico de seguridad sin revelar si el usuario existe o no (HU01)
    invalid_credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas. Verifique su usuario y contraseña."
    )

    if not user or not user.is_active:
        raise invalid_credentials_exc

    if not verify_password(req.password, user.password_hash):
        raise invalid_credentials_exc

    # Generar token con rol
    token = create_access_token({"sub": user.username, "role": user.role, "uid": user.id})
    permissions = list(ROLE_PERMISSIONS.get(user.role.upper(), []))

    return LoginResponse(
        access_token=token,
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        permissions=permissions
    )


@router.get("/me")
def get_profile(current_user: User = Depends(get_current_user)):
    """Retorna los datos del usuario autenticado."""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "permissions": list(ROLE_PERMISSIONS.get(current_user.role.upper(), []))
    }
