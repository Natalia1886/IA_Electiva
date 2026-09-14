"""Critical-flow integration tests (Prompt 20).

Runs against the DEDICATED test database provisioned by conftest.py — the real
store database is never touched. Covers the asked scenarios with the
mandatory negative cases:

- login/role control (+ salesperson blocked from admin endpoints)
- product CRUD
- complete sales flow with automatic stock deduction (and movement log)
- sale with INSUFFICIENT STOCK (rejected, inventory unchanged)
- inventory alerts (out of stock / low)
- digitized-sales plumbing: incomplete data and unknown-record rejection
- purchase recommendations (admin-only, explainable from real features)
"""
from datetime import date, timedelta
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

transport = ASGITransport(app=app)


@pytest.fixture
async def client():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def login(client, username: str, password: str) -> str:
    r = await client.post("/api/auth/login", data={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def any_product(client, token: str) -> dict:
    return (await client.get("/api/products", headers=auth(token))).json()[0]


# --- Login and role control ---------------------------------------------------

async def test_login_admin_ok_and_wrong_password_401(client):
    token = await login(client, "admin", "admin123")
    r = await client.get("/api/auth/me", headers=auth(token))
    assert r.status_code == 200
    assert r.json()["role"] == "admin"

    bad = await client.post("/api/auth/login", data={"username": "admin", "password": "incorrecta"})
    assert bad.status_code == 401


async def test_unauthenticated_request_rejected(client):
    assert (await client.get("/api/products")).status_code == 401
    assert (await client.get("/api/ai/recomendaciones")).status_code == 401


async def test_salesperson_blocked_from_admin_resources(client):
    seller = await login(client, "vendedor", "vendedor123")
    pid = (await any_product(client, seller))["id"]

    blocked = [
        ("get", "/api/users"),
        ("get", "/api/ai/recomendaciones"),
        ("get", "/api/ai/recommendations"),
        ("get", "/api/reports/dashboard"),
        ("post", "/api/products"),
        ("patch", f"/api/products/{pid}"),
        ("delete", f"/api/products/{pid}"),
        ("post", "/api/holidays"),
    ]
    for method, path in blocked:
        kwargs = {"headers": auth(seller)}
        if method in ("post", "patch"):
            kwargs["json"] = {}
        r = await getattr(client, method)(path, **kwargs)
        assert r.status_code == 403, f"{method.upper()} {path} -> {r.status_code}"


# --- Product CRUD -------------------------------------------------------------

async def test_product_crud_roundtrip(client):
    token = await login(client, "admin", "admin123")
    code = f"PRU-{uuid4().hex[:8].upper()}"
    r = await client.post("/api/products", headers=auth(token), json={
        "code": code, "name": "Producto Prompt 20", "price": 100, "cost": 40,
        "min_stock": 2, "stock": 5,
    })
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    r = await client.patch(f"/api/products/{pid}", headers=auth(token), json={"price": 150})
    assert r.status_code == 200 and r.json()["price"] == 150

    got = (await client.get(f"/api/products/{pid}", headers=auth(token))).json()
    assert got["code"] == code

    assert (await client.delete(f"/api/products/{pid}", headers=auth(token))).status_code == 204
    assert (await client.get(f"/api/products/{pid}", headers=auth(token))).status_code == 404

    r = await client.post(f"/api/products/{pid}/reactivate", headers=auth(token))
    assert r.status_code == 200 and r.json()["is_active"] is True
    await client.delete(f"/api/products/{pid}", headers=auth(token))


# --- Complete sales flow with stock deduction ---------------------------------

async def test_sale_deducts_stock_and_logs_movement(client):
    token = await login(client, "admin", "admin123")
    products = (await client.get("/api/products", headers=auth(token))).json()
    target = next(p for p in products if p["code"] == "ROS-001")
    pid, before = target["id"], target["stock"]

    r = await client.post("/api/sales", headers=auth(token), json={
        "sale_date": date.today().isoformat(),
        "payment_method": "cash",
        "items": [{"product_id": pid, "quantity": 4}],
    })
    assert r.status_code == 201, r.text
    sale = r.json()
    assert sale["total"] == 4 * target["price"]
    assert sale["source"] == "manual"

    after = (await client.get(f"/api/products/{pid}", headers=auth(token))).json()["stock"]
    assert after == before - 4  # stock deducted atomically

    moves = (await client.get(f"/api/inventory/movements?product_id={pid}", headers=auth(token))).json()
    sale_moves = [m for m in moves if m["movement_type"] == "sale" and m["reference_sale_id"] == sale["id"]]
    assert len(sale_moves) == 1 and sale_moves[0]["quantity"] == -4  # outgoing = negative

    mine = (await client.get(f"/api/sales?salesperson_id={sale['salesperson_id']}&limit=5",
                             headers=auth(token))).json()
    assert any(s["id"] == sale["id"] for s in mine)


async def test_sale_with_insufficient_stock_rejected(client):
    token = await login(client, "admin", "admin123")
    code = f"STK-{uuid4().hex[:8].upper()}"
    r = await client.post("/api/products", headers=auth(token), json={
        "code": code, "name": "Stock insuficiente", "price": 10, "min_stock": 1, "stock": 5,
    })
    pid = r.json()["id"]

    r = await client.post("/api/sales", headers=auth(token), json={
        "sale_date": date.today().isoformat(),
        "items": [{"product_id": pid, "quantity": 6}],
    })
    assert r.status_code == 400, r.text          # negative case: quantity > stock

    after = (await client.get(f"/api/products/{pid}", headers=auth(token))).json()["stock"]
    assert after == 5                            # inventory untouched
    moves = (await client.get(f"/api/inventory/movements?product_id={pid}", headers=auth(token))).json()
    assert not any(m["movement_type"] == "sale" for m in moves)

    await client.delete(f"/api/products/{pid}", headers=auth(token))


# --- Inventory alerts ---------------------------------------------------------

async def test_inventory_alerts_out_of_stock_and_low(client):
    token = await login(client, "admin", "admin123")
    codes = [f"ALR-{uuid4().hex[:6].upper()}", f"ALR-{uuid4().hex[:6].upper()}"]
    stocks = [(0, 1), (2, 2)]
    pids = []
    for code, (stock, min_stock) in zip(codes, stocks):
        r = await client.post("/api/products", headers=auth(token), json={
            "code": code, "name": f"Alerta {code}", "price": 10, "min_stock": min_stock, "stock": stock,
        })
        assert r.status_code == 201, r.text
        pids.append(r.json()["id"])

    alerts = (await client.get("/api/inventory/alerts", headers=auth(token))).json()
    by_id = {a["product_id"]: a for a in alerts}
    assert pids[0] in by_id and by_id[pids[0]]["stock_status"] == "out_of_stock"
    assert pids[1] in by_id and by_id[pids[1]]["stock_status"] == "low"

    for pid in pids:
        await client.delete(f"/api/products/{pid}", headers=auth(token))


# --- Digitized-sales plumbing (AI photo upload removed) ------------------------

async def test_digitized_sale_rejects_empty_and_unknown_record(client):
    token = await login(client, "admin", "admin123")

    # Cannot confirm an empty import as a sale (schema-level validation).
    bad = await client.post("/api/sales", headers=auth(token), json={
        "sale_date": date.today().isoformat(),
        "digitization_id": 999999,
        "items": [],
    })
    assert bad.status_code == 422

    # Unknown digitization record -> rejected, nothing recorded.
    orphan = await client.post("/api/sales", headers=auth(token), json={
        "sale_date": date.today().isoformat(),
        "digitization_id": 999999,
        "items": [{"product_id": 1, "quantity": 1}],
    })
    assert orphan.status_code == 400


# --- Purchase recommendations -------------------------------------------------

async def test_recommendations_admin_only_and_explainable(client):
    token = await login(client, "admin", "admin123")
    body = (await client.get("/api/ai/recomendaciones", headers=auth(token))).json()
    assert body["items"], "seeded store must yield recommendations on the test DB"
    for item in body["items"]:
        assert item["reason"]                       # explanation derives from real features
        assert item["estimated_demand"] >= 0

    seller = await login(client, "vendedor", "vendedor123")
    assert (await client.get("/api/ai/recomendaciones", headers=auth(seller))).status_code == 403


async def test_recommendations_consume_admin_holiday_factor(client):
    token = await login(client, "admin", "admin123")
    products = (await client.get("/api/products", headers=auth(token))).json()
    target = next(p for p in products if p["code"] == "ROS-001")  # no seeded feast -> deterministic
    start = date.today() + timedelta(days=2)
    r = await client.post("/api/holidays", headers=auth(token), json={
        "name": f"Factor20 {uuid4().hex[:8]}",
        "start_date": start.isoformat(),
        "end_date": start.isoformat(),
        "expected_demand_factor": 3.0,
        "product_ids": [target["id"]],
    })
    assert r.status_code == 201, r.text
    hid = r.json()["id"]

    body = (await client.get("/api/ai/recomendaciones", headers=auth(token))).json()
    item = next((i for i in body["items"] if i["code"] == "ROS-001"), None)
    assert item is not None
    assert "factor de demanda esperada x3.0" in item["reason"]

    await client.delete(f"/api/holidays/{hid}", headers=auth(token))