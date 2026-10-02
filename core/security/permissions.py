"""Matriz de permisos por rol (RF02, RNF04).
Define qué acciones están permitidas para 'ADMIN' y 'VENDEDOR'.
"""

from typing import Set

ROLE_PERMISSIONS = {
    "ADMIN": {
        "auth:login",
        "products:view",
        "products:create",
        "products:edit",
        "products:deactivate",
        "sales:create",
        "sales:view_daily",
        "inventory:view",
        "inventory:alerts",
        "inventory:movements",
        "festivities:manage",
        "recommendations:view",
        "recommendations:train",
        "dashboard:view",
    },
    "VENDEDOR": {
        "auth:login",
        "products:view",
        "sales:create",
        "sales:view_daily",
        "dashboard:view_limited",
    }
}


def check_permission(role: str, permission: str) -> bool:
    """Verifica si un rol tiene permitido ejecutar una acción determinada."""
    role_upper = (role or "").upper()
    perms: Set[str] = ROLE_PERMISSIONS.get(role_upper, set())
    return permission in perms


def is_admin(role: str) -> bool:
    """Valida si el rol es Administrador."""
    return (role or "").upper() == "ADMIN"
