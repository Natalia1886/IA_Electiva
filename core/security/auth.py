"""Seguridad, autenticación y hash de contraseñas (RF01, RF02, RNF03, RNF04)."""

import hashlib
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt

SECRET_KEY = os.getenv("APP_SECRET_KEY", "milan_framework_religious_store_secret_key_2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12  # 12 horas


def hash_password(password: str) -> str:
    """Genera hash seguro PBKDF2-HMAC-SHA256 con salt aleatorio (RNF03)."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations=100000
    )
    return f"{salt}:{key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña en texto plano coincide con el hash almacenado."""
    try:
        salt, stored_hash = hashed_password.split(":")
        new_key = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations=100000
        )
        return secrets.compare_digest(new_key.hex(), stored_hash)
    except Exception:
        return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Crea token JWT con rol y expiración para validación en backend (RNF04)."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodifica y valida un token JWT."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        return None
