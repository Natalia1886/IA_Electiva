"""Declarative role-based authorization matrix.

Single source of truth for which role may perform what action in each
resource. Routing code never repeats ``if role == ...`` checks; instead it
declares the required permission per endpoint (see ``app.api.deps``).

Permission matrix (admin / salesperson):

| Functionality        | Admin | Salesperson |
|----------------------|:-----:|:-----------:|
| View products        |   ✓   |      ✓      |
| Add products         |   ✓   |      ✗      |
| Edit products        |   ✓   |      ✗      |
| Delete products      |   ✓   |      ✗      |
| Register sales       |   ✓   |      ✓      |
| View inventory       | full  |  limited*   |
| View recommendations |   ✓   |      ✗      |
| Manage users         |   ✓   |      ✗      |

* The salesperson may view the current stock status only. Purchase alerts and
  the full movement history are out of their reach (admin-only), which is why
  their views are split into three explicit permissions below.
"""
from __future__ import annotations

ADMIN = "admin"
SALESPERSON = "salesperson"

# permission -> roles allowed to exercise it
PERMISSIONS: dict[str, frozenset[str]] = {
    # products
    "products:view": frozenset({ADMIN, SALESPERSON}),
    "products:manage": frozenset({ADMIN}),
    # sales
    "sales:view": frozenset({ADMIN, SALESPERSON}),
    "sales:register": frozenset({ADMIN, SALESPERSON}),
    # inventory — the salesperson only gets the *limited* view
    "inventory:view:limited": frozenset({ADMIN, SALESPERSON}),  # current stock only
    "inventory:view:alerts": frozenset({ADMIN}),  # purchase alerts
    "inventory:view:history": frozenset({ADMIN}),  # full movement history
    "inventory:manage": frozenset({ADMIN}),  # manual stock adjustments
    # recommendations
    "recommendations:view": frozenset({ADMIN}),
    # users
    "users:manage": frozenset({ADMIN}),
}


def roles_for(permission: str) -> frozenset[str]:
    """Return the set of roles allowed to exercise ``permission``."""
    return PERMISSIONS.get(permission, frozenset())


def can(role: str, permission: str) -> bool:
    """Whether ``role`` may exercise ``permission``."""
    return role in PERMISSIONS.get(permission, frozenset())