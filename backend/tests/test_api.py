"""Integration tests against the running PostgreSQL database.

Requires the Docker Postgres instance to be up and seeded:
    docker compose up -d && python -m app.seed
"""
import uuid
from datetime import date, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.main import app

transport = ASGITransport(app=app)


@pytest.fixture
async def client():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _login(client, username: str, password: str) -> str:
    r = await client.post("/api/auth/login", data={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def test_login_and_me(client):
    token = await _login(client, "admin", "admin123")
    r = await client.get("/api/auth/me", headers=_auth(token))
    assert r.status_code == 200
    body = r.json()
    assert body["username"] == "admin"
    assert body["role"] == "admin"


async def test_products_list(client):
    token = await _login(client, "admin", "admin123")
    r = await client.get("/api/products", headers=_auth(token))
    assert r.status_code == 200
    products = r.json()
    assert len(products) >= 14
    first = products[0]
    assert {"id", "code", "name", "price", "stock", "min_stock", "low_stock"} <= set(first)


async def test_duplicate_product_code_rejected(client):
    token = await _login(client, "admin", "admin123")
    r = await client.post(
        "/api/products",
        headers=_auth(token),
        json={"code": "VIR-001", "name": "Duplicado", "price": 10},
    )
    assert r.status_code == 400


async def test_salesperson_cannot_create_product(client):
    token = await _login(client, "vendedor", "vendedor123")
    r = await client.post(
        "/api/products",
        headers=_auth(token),
        json={"code": "X-1", "name": "No autorizado", "price": 1},
    )
    assert r.status_code == 403


async def test_unauthorized_requests_rejected(client):
    r = await client.get("/api/products")
    assert r.status_code == 401


async def test_sale_flow_deducs_stock(client):
    token = await _login(client, "admin", "admin123")
    products = (await client.get("/api/products", headers=_auth(token))).json()
    target = next(p for p in products if p["code"] == "ROS-001")
    before = target["stock"]

    r = await client.post(
        "/api/sales",
        headers=_auth(token),
        json={"sale_date": "2026-09-13", "items": [{"product_id": target["id"], "quantity": 2}]},
    )
    assert r.status_code == 201, r.text
    sale = r.json()
    assert sale["total"] == round(target["price"] * 2, 2)
    assert sale["item_count"] == 1

    after = (await client.get(f"/api/products/{target['id']}", headers=_auth(token))).json()["stock"]
    assert after == before - 2


async def test_insufficient_stock_rejected(client):
    token = await _login(client, "admin", "admin123")
    products = (await client.get("/api/products", headers=_auth(token))).json()
    target = next(p for p in products if p["code"] == "VEL-004")
    before = target["stock"]

    sales_before = (await client.get("/api/sales", headers=_auth(token))).json()
    movements_before = [
        m for m in (await client.get("/api/inventory/movements", headers=_auth(token))).json()
        if m["product_id"] == target["id"]
    ]

    r = await client.post(
        "/api/sales",
        headers=_auth(token),
        json={"sale_date": "2026-09-13", "items": [{"product_id": target["id"], "quantity": 9999}]},
    )
    assert r.status_code == 400

    # Rollback guarantee: nothing persisted — stock, sale list and movement log unchanged.
    after = (await client.get(f"/api/products/{target['id']}", headers=_auth(token))).json()["stock"]
    assert after == before
    sales_after = (await client.get("/api/sales", headers=_auth(token))).json()
    assert len(sales_after) == len(sales_before)
    movements_after = [
        m for m in (await client.get("/api/inventory/movements", headers=_auth(token))).json()
        if m["product_id"] == target["id"]
    ]
    assert len(movements_after) == len(movements_before)


async def test_empty_items_rejected(client):
    token = await _login(client, "admin", "admin123")
    r = await client.post(
        "/api/sales",
        headers=_auth(token),
        json={"sale_date": "2026-09-13", "items": []},
    )
    assert r.status_code == 422


async def test_multi_item_sale_totals_and_stock(client):
    token = await _login(client, "admin", "admin123")
    products = {p["code"]: p for p in (await client.get("/api/products", headers=_auth(token))).json()}
    a, b = products["VEL-002"], products["VEL-003"]
    a_before = a["stock"]
    b_before = b["stock"]

    r = await client.post(
        "/api/sales",
        headers=_auth(token),
        json={
            "sale_date": "2026-09-12",
            "items": [
                {"product_id": a["id"], "quantity": 2},
                {"product_id": b["id"], "quantity": 3},
            ],
        },
    )
    assert r.status_code == 201, r.text
    sale = r.json()
    expected = round(a["price"] * 2 + b["price"] * 3, 2)
    assert sale["total"] == expected
    assert sale["item_count"] == 2

    stocks = {p["code"]: p["stock"] for p in (await client.get("/api/products", headers=_auth(token))).json()}
    assert stocks[a["code"]] == a_before - 2
    assert stocks[b["code"]] == b_before - 3

    movements = (await client.get("/api/inventory/movements", headers=_auth(token))).json()
    sale_movements = [m for m in movements if m["reference_sale_id"] == sale["id"]]
    assert len(sale_movements) == 2
    assert {m["product_id"] for m in sale_movements} == {a["id"], b["id"]}


async def test_sale_records_salesperson(client):
    admin = await _login(client, "admin", "admin123")
    admin_id = (await client.get("/api/auth/me", headers=_auth(admin))).json()["id"]
    seller = await _login(client, "vendedor", "vendedor123")
    products = (await client.get("/api/products", headers=_auth(admin))).json()
    target = next(p for p in products if p["code"] == "ROS-002")

    r = await client.post(
        "/api/sales",
        headers=_auth(seller),
        json={"sale_date": "2026-09-13", "items": [{"product_id": target["id"], "quantity": 1}]},
    )
    assert r.status_code == 201
    assert r.json()["salesperson_id"] is not None
    assert r.json()["salesperson_id"] != admin_id


async def test_salesperson_listing_scoped_to_own_sales(client):
    seller = await _login(client, "vendedor", "vendedor123")
    admin = await _login(client, "admin", "admin123")
    admin_id = (await client.get("/api/auth/me", headers=_auth(admin))).json()["id"]
    seller_id = (await client.get("/api/auth/me", headers=_auth(seller))).json()["id"]
    products = (await client.get("/api/products", headers=_auth(admin))).json()
    target = next(p for p in products if p["code"] == "NAC-001")

    r = await client.post(
        "/api/sales",
        headers=_auth(seller),
        json={"sale_date": "2026-09-13", "items": [{"product_id": target["id"], "quantity": 1}]},
    )
    assert r.status_code == 201

    # Attempting to ask for another user's sales is silently pinned to own id.
    mine = (await client.get("/api/sales", headers=_auth(seller))).json()
    pinned = (
        await client.get(f"/api/sales?salesperson_id={admin_id}", headers=_auth(seller))
    ).json()
    assert all(s["salesperson_id"] == seller_id for s in mine)
    assert [s["id"] for s in mine] == [s["id"] for s in pinned]

    # The admin, meanwhile, still filters freely.
    others = (
        await client.get(f"/api/sales?salesperson_id={admin_id}", headers=_auth(admin))
    ).json()
    assert all(s["salesperson_id"] == admin_id for s in others)


async def test_sale_stores_payment_method(client):
    token = await _login(client, "admin", "admin123")
    products = (await client.get("/api/products", headers=_auth(token))).json()
    target = next(p for p in products if p["code"] == "ROS-002")

    r = await client.post(
        "/api/sales",
        headers=_auth(token),
        json={
            "sale_date": "2026-09-13",
            "items": [{"product_id": target["id"], "quantity": 1}],
            "payment_method": "card",
        },
    )
    assert r.status_code == 201
    assert r.json()["payment_method"] == "card"

    # Defaults to cash when omitted.
    r2 = await client.post(
        "/api/sales",
        headers=_auth(token),
        json={"sale_date": "2026-09-13", "items": [{"product_id": target["id"], "quantity": 1}]},
    )
    assert r2.status_code == 201
    assert r2.json()["payment_method"] == "cash"

    bad = await client.post(
        "/api/sales",
        headers=_auth(token),
        json={
            "sale_date": "2026-09-13",
            "items": [{"product_id": target["id"], "quantity": 1}],
            "payment_method": "bitcoin",
        },
    )
    assert bad.status_code == 422


async def test_sale_appears_in_daily_summary(client):
    token = await _login(client, "admin", "admin123")
    products = (await client.get("/api/products", headers=_auth(token))).json()
    target = next(p for p in products if p["code"] == "VIR-001")

    before = (await client.get("/api/sales/daily/2026-09-11", headers=_auth(token))).json()
    r = await client.post(
        "/api/sales",
        headers=_auth(token),
        json={"sale_date": "2026-09-11", "items": [{"product_id": target["id"], "quantity": 3}]},
    )
    assert r.status_code == 201

    after = (await client.get("/api/sales/daily/2026-09-11", headers=_auth(token))).json()
    assert after["transaction_count"] == before["transaction_count"] + 1
    assert after["units_sold"] == before["units_sold"] + 3
    assert before["total_value"] + round(target["price"] * 3, 2) == after["total_value"]
    top = next(p for p in after["top_products"] if p["product_id"] == target["id"])
    assert top["units_sold"] >= 3


async def test_daily_summary_structure(client):
    token = await _login(client, "admin", "admin123")
    r = await client.get("/api/sales/daily/2026-09-13", headers=_auth(token))
    assert r.status_code == 200
    body = r.json()
    assert {"total_value", "transaction_count", "units_sold", "top_products"} <= set(body)


async def test_inventory_alerts(client):
    token = await _login(client, "admin", "admin123")
    r = await client.get("/api/inventory/alerts", headers=_auth(token))
    assert r.status_code == 200
    codes = [a["code"] for a in r.json()]
    assert "VEL-004" in codes


async def test_dashboard_admin_only(client):
    admin = await _login(client, "admin", "admin123")
    r = await client.get("/api/reports/dashboard", headers=_auth(admin))
    assert r.status_code == 200
    body = r.json()
    assert {"today_sales_value", "week_trend", "low_stock_products", "top_products_30d"} <= set(body)

    seller = await _login(client, "vendedor", "vendedor123")
    r = await client.get("/api/reports/dashboard", headers=_auth(seller))
    assert r.status_code == 403


async def test_recommendations_structure(client):
    token = await _login(client, "admin", "admin123")
    r = await client.get("/api/ai/recommendations", headers=_auth(token))
    assert r.status_code == 200
    body = r.json()
    assert body["source"]
    assert body["items"]
    item = body["items"][0]
    assert {"suggested_quantity", "rationale", "reason", "estimated_demand",
            "current_stock", "min_stock"} <= set(item)
    assert item["estimated_demand"] >= 0

    seller = await _login(client, "vendedor", "vendedor123")
    r = await client.get("/api/ai/recommendations", headers=_auth(seller))
    assert r.status_code == 403


async def test_recomendaciones_alias_admin_only(client):
    token = await _login(client, "admin", "admin123")
    r = await client.get("/api/ai/recomendaciones", headers=_auth(token))
    assert r.status_code == 200
    body = r.json()
    assert body["items"]
    item = body["items"][0]
    assert item["estimated_demand"] >= 0
    assert item["reason"]  # the explanation must derive from real features

    seller = await _login(client, "vendedor", "vendedor123")
    r = await client.get("/api/ai/recomendaciones", headers=_auth(seller))
    assert r.status_code == 403


async def _seed_digitization_record(status: str = "awaiting_review", raw_data: list | None = None) -> int:
    """Create a digitization record directly in the test DB.

    The AI photo-upload endpoint was removed, but digitized (historical) sales
    via ``digitization_id`` are still supported, so the sales-side plumbing is
    exercised by seeding the record by hand.
    """
    from app.database import async_session_factory
    from app.models.digitization import DigitizationRecord
    from app.models.user import User

    async with async_session_factory() as s:
        admin_id = (await s.execute(select(User.id).where(User.username == "admin"))).scalar_one()
        rec = DigitizationRecord(
            original_filename="cuaderno.jpg",
            status=status,
            analyzer="mock-baseline",
            raw_data=raw_data,
            uploaded_by=admin_id,
        )
        s.add(rec)
        await s.commit()
        return rec.id


async def test_digitized_sale_flow_and_correction_stats(client):
    token = await _login(client, "admin", "admin123")
    products = (await client.get("/api/products", headers=_auth(token))).json()
    p1 = next(p for p in products if p["code"] == "ROS-001")
    p2 = next(p for p in products if p["code"] == "VEL-001")
    stock_before = p1["stock"]

    rid = await _seed_digitization_record(
        raw_data=[{"date": "2026-09-12", "product_code": "ROS-001", "quantity": 1, "unit_price": 10.0}]
    )

    # The digitized rows exceed current stock: that must be fine, the notebook
    # describes HISTORICAL sales and current stock is never consumed.
    r = await client.post(
        "/api/sales",
        headers=_auth(token),
        json={
            "sale_date": "2026-09-12",
            "payment_method": "cash",
            "digitization_id": rid,
            "items": [
                {"product_id": p1["id"], "quantity": stock_before + 5, "unit_price": 12.5},
                {"product_id": p2["id"], "quantity": 1},
            ],
        },
    )
    assert r.status_code == 201, r.text
    sale = r.json()
    assert sale["source"] == "digitized"
    assert sale["digitization_id"] == rid

    detail = (await client.get(f"/api/sales/{sale['id']}", headers=_auth(token))).json()
    line = next(li for li in detail["items"] if li["product_id"] == p1["id"])
    assert line["unit_price"] == 12.5  # reviewed price takes precedence over catalog
    line2 = next(li for li in detail["items"] if li["product_id"] == p2["id"])
    assert line2["unit_price"] == p2["price"]  # omitted override falls back to catalog

    # Stock untouched: historical digitization must not move current inventory.
    after = (await client.get("/api/products", headers=_auth(token))).json()
    p1_after = next(p for p in after if p["code"] == "ROS-001")
    assert p1_after["stock"] == stock_before

    from app.database import async_session_factory
    from app.models.digitization import DigitizationRecord

    async with async_session_factory() as s:
        rec = await s.get(DigitizationRecord, rid)
        assert rec.status == "imported"
        assert rec.correction_stats is not None
        assert rec.correction_stats["rows_confirmed"] == 2


async def test_digitized_record_imported_twice_rejected(client):
    token = await _login(client, "admin", "admin123")
    products = (await client.get("/api/products", headers=_auth(token))).json()
    p1 = next(p for p in products if p["code"] == "ROS-001")
    rid = await _seed_digitization_record()

    ok = await client.post(
        "/api/sales",
        headers=_auth(token),
        json={"sale_date": "2026-09-11", "digitization_id": rid,
              "items": [{"product_id": p1["id"], "quantity": 1}]},
    )
    assert ok.status_code == 201

    again = await client.post(
        "/api/sales",
        headers=_auth(token),
        json={"sale_date": "2026-09-11", "digitization_id": rid,
              "items": [{"product_id": p1["id"], "quantity": 1}]},
    )
    assert again.status_code == 400


async def test_digitized_sale_unknown_record_rejected(client):
    token = await _login(client, "admin", "admin123")
    products = (await client.get("/api/products", headers=_auth(token))).json()
    p1 = next(p for p in products if p["code"] == "ROS-001")
    r = await client.post(
        "/api/sales",
        headers=_auth(token),
        json={"sale_date": "2026-09-10", "digitization_id": 999999,
              "items": [{"product_id": p1["id"], "quantity": 1}]},
    )
    assert r.status_code == 400


# --- Centralized error handling -------------------------------------------------

async def test_unknown_route_returns_structured_404(client):
    r = await client.get("/api/does-not-exist")
    assert r.status_code == 404
    assert r.json() == {"detail": "Not Found"}


async def test_validation_errors_return_structured_422(client):
    token = await _login(client, "admin", "admin123")
    r = await client.post(
        "/api/products",
        headers=_auth(token),
        json={"code": "X-999", "name": "Inválido", "price": -5},
    )
    assert r.status_code == 422
    assert isinstance(r.json()["detail"], list)


async def test_unauthorized_body_is_structured(client):
    r = await client.get("/api/products")
    assert r.status_code == 401
    assert "detail" in r.json()


async def test_conflict_on_duplicate_category(client):
    token = await _login(client, "admin", "admin123")
    r = await client.post(
        "/api/categories",
        headers=_auth(token),
        json={"name": "Imágenes religiosas"},
    )
    assert r.status_code == 400


# --- Role-based permission matrix (Prompt 7) -----------------------------------

def test_permission_matrix_mapping():
    from app.core.permissions import can

    assert can("admin", "products:view")
    assert can("salesperson", "products:view")
    assert can("admin", "products:manage")
    assert not can("salesperson", "products:manage")
    assert can("salesperson", "sales:register")
    assert can("salesperson", "inventory:view:limited")
    assert can("admin", "inventory:view:limited")
    assert not can("salesperson", "inventory:view:alerts")
    assert not can("salesperson", "inventory:view:history")
    assert can("admin", "inventory:view:alerts")
    assert can("admin", "inventory:view:history")
    assert not can("salesperson", "recommendations:view")
    assert can("admin", "recommendations:view")
    assert not can("salesperson", "users:manage")


async def test_salesperson_can_view_current_stock(client):
    token = await _login(client, "vendedor", "vendedor123")
    r = await client.get("/api/inventory", headers=_auth(token))
    assert r.status_code == 200
    assert "stock" in r.json()[0]
    r = await client.get("/api/inventory/position", headers=_auth(token))
    assert r.status_code == 200


async def test_salesperson_cannot_view_alerts(client):
    token = await _login(client, "vendedor", "vendedor123")
    r = await client.get("/api/inventory/alerts", headers=_auth(token))
    assert r.status_code == 403


async def test_salesperson_cannot_view_movement_history(client):
    token = await _login(client, "vendedor", "vendedor123")
    r = await client.get("/api/inventory/movements", headers=_auth(token))
    assert r.status_code == 403


async def test_salesperson_cannot_adjust_stock(client):
    token = await _login(client, "vendedor", "vendedor123")
    r = await client.post(
        "/api/inventory/movements",
        headers=_auth(token),
        json={"product_id": 1, "quantity": 5, "movement_type": "purchase"},
    )
    assert r.status_code == 403


async def test_salesperson_can_register_sale(client):
    token = await _login(client, "vendedor", "vendedor123")
    products = (await client.get("/api/products", headers=_auth(token))).json()
    target = next(p for p in products if p["code"] == "ROS-001")
    r = await client.post(
        "/api/sales",
        headers=_auth(token),
        json={"sale_date": "2026-09-13", "items": [{"product_id": target["id"], "quantity": 1}]},
    )
    assert r.status_code == 201, r.text
    assert r.json()["salesperson_name"] is None


async def test_products_management_admin_only(client):
    seller = await _login(client, "vendedor", "vendedor123")
    admin = await _login(client, "admin", "admin123")
    products = (await client.get("/api/products", headers=_auth(admin))).json()
    pid = next(p for p in products if p["code"] == "ROS-001")["id"]

    r = await client.patch(
        f"/api/products/{pid}",
        headers=_auth(seller),
        json={"price": 9999},
    )
    assert r.status_code == 403
    r = await client.delete(f"/api/products/{pid}", headers=_auth(seller))
    assert r.status_code == 403


async def test_salesperson_cannot_manage_users(client):
    token = await _login(client, "vendedor", "vendedor123")
    r = await client.get("/api/users", headers=_auth(token))
    assert r.status_code == 403


# --- Product CRUD (Prompt 8) ---------------------------------------------------

async def test_products_views_for_both_roles(client):
    admin = await _login(client, "admin", "admin123")
    seller = await _login(client, "vendedor", "vendedor123")
    products = (await client.get("/api/products", headers=_auth(admin))).json()
    assert len(products) >= 14
    r = await client.get("/api/products?include_inactive=true", headers=_auth(admin))
    assert r.status_code == 200
    assert len(r.json()) >= len(products)
    r = await client.get("/api/products", headers=_auth(seller))
    assert r.status_code == 200


async def test_products_search_and_filters(client):
    token = await _login(client, "admin", "admin123")

    r = await client.get("/api/products?search=ROS", headers=_auth(token))
    codes = [p["code"] for p in r.json()]
    assert "ROS-001" in codes and "VIR-001" not in codes

    r = await client.get("/api/products?search=Vela", headers=_auth(token))
    assert len(r.json()) >= 1

    r = await client.get("/api/products?low_stock=true", headers=_auth(token))
    assert r.status_code == 200
    assert all(p["low_stock"] for p in r.json())

    r = await client.get("/api/products?holiday_id=1", headers=_auth(token))
    assert r.status_code == 200

    first = (await client.get("/api/products", headers=_auth(token))).json()[0]
    pid = first["id"]
    got = (await client.get(f"/api/products/{pid}", headers=_auth(token))).json()
    assert got["id"] == pid


async def test_products_category_filter(client):
    token = await _login(client, "admin", "admin123")
    categories = (await client.get("/api/categories", headers=_auth(token))).json()
    rosarios = next(c for c in categories if c["name"] == "Rosarios")
    r = await client.get(f"/api/products?category_id={rosarios['id']}", headers=_auth(token))
    codes = {p["code"] for p in r.json()}
    assert "ROS-001" in codes and "VEL-001" not in codes


async def test_product_soft_delete_and_reactivate(client):
    token = await _login(client, "admin", "admin123")
    products = (await client.get("/api/products?include_inactive=true", headers=_auth(token))).json()
    target = next(p for p in products if p["code"] == "GRA-001")
    pid = target["id"]

    r = await client.delete(f"/api/products/{pid}", headers=_auth(token))
    assert r.status_code == 204

    listed = {p["id"] for p in (await client.get("/api/products", headers=_auth(token))).json()}
    assert pid not in listed
    inactive = (await client.get("/api/products?include_inactive=true", headers=_auth(token))).json()
    assert any(p["id"] == pid and not p["is_active"] for p in inactive)

    r = await client.post(f"/api/products/{pid}/reactivate", headers=_auth(token))
    assert r.status_code == 200
    assert r.json()["is_active"] is True


async def test_product_update_full_flow(client):
    token = await _login(client, "admin", "admin123")
    payload = {
        "code": f"TST-{abs(hash('u')) % 100000}",
        "name": "Producto de prueba",
        "price": 50,
        "cost": 30,
        "min_stock": 2,
        "stock": 10,
    }
    r = await client.post("/api/products", headers=_auth(token), json=payload)
    assert r.status_code == 201, r.text
    created = r.json()

    r = await client.patch(f"/api/products/{created['id']}", headers=_auth(token), json={"price": 60})
    assert r.status_code == 200
    assert r.json()["price"] == 60
    assert r.json()["name"] == payload["name"]

    r = await client.get(f"/api/products/{created['id']}", headers=_auth(token))
    assert r.status_code == 200
    assert r.json()["code"] == payload["code"]

    r = await client.delete(f"/api/products/{created['id']}", headers=_auth(token))
    assert r.status_code == 204
    r = await client.get(f"/api/products/{created['id']}", headers=_auth(token))
    assert r.status_code == 404

    r = await client.post(f"/api/products/{created['id']}/reactivate", headers=_auth(token))
    assert r.status_code == 200
    assert r.json()["is_active"] is True


# --- Inventory three-level status (Prompt 10) ----------------------------------

def test_compute_stock_status_pure():
    from app.core.stock_status import compute_stock_status

    assert compute_stock_status(0, 5) == "out_of_stock"
    assert compute_stock_status(5, 5) == "low"
    assert compute_stock_status(3, 5) == "low"
    assert compute_stock_status(1, 0) == "normal"
    assert compute_stock_status(6, 5) == "normal"
    assert compute_stock_status(0, 0) == "out_of_stock"


async def test_inventory_status_has_stock_status(client):
    token = await _login(client, "admin", "admin123")
    items = (await client.get("/api/inventory", headers=_auth(token))).json()
    assert items
    for item in items:
        expected = (
            "out_of_stock" if item["stock"] == 0
            else "low" if item["stock"] <= item["min_stock"]
            else "normal"
        )
        assert item["stock_status"] == expected


async def test_alerts_include_low_and_out_of_stock(client):
    token = await _login(client, "admin", "admin123")
    code = f"AGO-{uuid.uuid4().hex[:8].upper()}"
    r = await client.post(
        "/api/products",
        headers=_auth(token),
        json={"code": code, "name": "Agotado test", "price": 10, "min_stock": 2, "stock": 0},
    )
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    alerts = (await client.get("/api/inventory/alerts", headers=_auth(token))).json()
    by_id = {a["product_id"]: a for a in alerts}
    assert pid in by_id
    assert by_id[pid]["stock_status"] == "out_of_stock"
    assert by_id[pid]["out_of_stock"] is True
    assert any(a["code"] == "VEL-004" and a["stock_status"] == "low" for a in alerts)

    await client.delete(f"/api/products/{pid}", headers=_auth(token))


async def test_manual_entry_updates_stock_and_logs_movement(client):
    token = await _login(client, "admin", "admin123")
    products = {p["code"]: p for p in (await client.get("/api/products", headers=_auth(token))).json()}
    target = products["VEL-002"]
    before = target["stock"]

    r = await client.post(
        "/api/inventory/movements",
        headers=_auth(token),
        json={"product_id": target["id"], "quantity": 25, "movement_type": "purchase", "reason": "Compra #999"},
    )
    assert r.status_code == 201, r.text
    mv = r.json()
    assert mv["product_id"] == target["id"]
    assert mv["quantity"] == 25
    assert mv["reference_sale_id"] is None
    assert mv["movement_type"] == "purchase"

    stock_after = (await client.get(f"/api/products/{target['id']}", headers=_auth(token))).json()["stock"]
    assert stock_after == before + 25

    movements = (await client.get(f"/api/inventory/movements?product_id={target['id']}", headers=_auth(token))).json()
    assert movements[0]["id"] == mv["id"]
    assert movements[0]["reason"] == "Compra #999"


async def test_manual_entry_rejects_negative_stock(client):
    token = await _login(client, "admin", "admin123")
    products = {p["code"]: p for p in (await client.get("/api/products", headers=_auth(token))).json()}
    target = products["NAC-001"]  # small stock
    r = await client.post(
        "/api/inventory/movements",
        headers=_auth(token),
        json={"product_id": target["id"], "quantity": 99999, "movement_type": "adjustment"},
    )
    assert r.status_code == 400


async def test_movement_history_filters(client):
    token = await _login(client, "admin", "admin123")
    r = await client.get("/api/inventory/movements?movement_type=sale&limit=5", headers=_auth(token))
    assert r.status_code == 200
    assert all(m["movement_type"] == "sale" for m in r.json())
    r = await client.get("/api/inventory/movements?limit=5", headers=_auth(token))
    assert len(r.json()) == 5


# --- Religious holidays CRUD (Prompt 18) --------------------------------------

async def _holiday_default_payload(client):
    token = await _login(client, "admin", "admin123")
    products = (await client.get("/api/products", headers=_auth(token))).json()
    ros_id = next(p["id"] for p in products if p["code"] == "ROS-001")
    vel_id = next(p["id"] for p in products if p["code"] == "VEL-001")
    return {
        "name": "Feriado Test",
        "day": 15,
        "month": 9,
        "expected_demand_factor": 2.0,
        "description": "Prueba Prompt 18",
        "product_ids": [ros_id, vel_id],
    }


async def test_holidays_crud_admin_only(client):
    token = await _login(client, "admin", "admin123")
    payload = {
        "name": f"Feriado CRUD {uuid.uuid4().hex[:8]}",
        "day": 20,
        "month": 11,
        "expected_demand_factor": 1.5,
        "product_ids": [],
    }
    r = await client.post("/api/holidays", headers=_auth(token), json=payload)
    assert r.status_code == 201, r.text
    created = r.json()
    assert created["expected_demand_factor"] == 1.5
    assert created["is_active"] is True
    assert created["products"] == []

    r = await client.patch(
        f"/api/holidays/{created['id']}",
        headers=_auth(token),
        json={"expected_demand_factor": 2.5},
    )
    assert r.status_code == 200
    assert r.json()["expected_demand_factor"] == 2.5

    r = await client.get("/api/holidays", headers=_auth(token))
    assert r.status_code == 200
    assert next(h for h in r.json() if h["id"] == created["id"])["expected_demand_factor"] == 2.5

    r = await client.delete(f"/api/holidays/{created['id']}", headers=_auth(token))
    assert r.status_code == 204
    assert next(h for h in (await client.get("/api/holidays", headers=_auth(token))).json()
                if h["id"] == created["id"])["is_active"] is False

    seller = await _login(client, "vendedor", "vendedor123")
    assert (await client.post("/api/holidays", headers=_auth(seller), json=payload)).status_code == 403
    assert (await client.patch(f"/api/holidays/{created['id']}", headers=_auth(seller),
                               json={"name": "X"})).status_code == 403
    assert (await client.delete(f"/api/holidays/{created['id']}", headers=_auth(seller))).status_code == 403


async def test_holiday_requires_occurrence_source(client):
    token = await _login(client, "admin", "admin123")
    name = uuid.uuid4().hex[:8]

    r = await client.post("/api/holidays", headers=_auth(token), json={"name": f"A {name}"})
    assert r.status_code == 400
    assert "fecha" in r.json()["detail"].lower()

    r = await client.post("/api/holidays", headers=_auth(token), json={"name": f"B {name}", "day": 15})
    assert r.status_code == 400

    r = await client.post("/api/holidays", headers=_auth(token), json={"name": f"C {name}", "month": 9})
    assert r.status_code == 400

    r = await client.post("/api/holidays", headers=_auth(token), json={
        "name": f"D {name}", "variable_date_code": "corpus_christi",
    })
    assert r.status_code == 201, r.text
    assert r.json()["day"] is None and r.json()["month"] is None
    await client.delete(f"/api/holidays/{r.json()['id']}", headers=_auth(token))


async def test_holiday_links_multiple_products(client):
    token = await _login(client, "admin", "admin123")
    payload = await _holiday_default_payload(client)
    payload["name"] = f"Multi Fest {uuid.uuid4().hex[:8]}"
    r = await client.post("/api/holidays", headers=_auth(token), json=payload)
    assert r.status_code == 201, r.text
    created = r.json()
    assert {p["code"] for p in created["products"]} == {"ROS-001", "VEL-001"}

    unknown = await client.post("/api/holidays", headers=_auth(token), json={
        "name": f"Multi Bad {uuid.uuid4().hex[:8]}",
        "day": 10,
        "month": 10,
        "product_ids": [999999],
    })
    assert unknown.status_code == 400
    assert "no encontrado" in unknown.json()["detail"]

    await client.delete(f"/api/holidays/{created['id']}", headers=_auth(token))


async def test_holiday_explicit_dates_ok(client):
    token = await _login(client, "admin", "admin123")
    start = date.today() + timedelta(days=10)
    end = start + timedelta(days=3)
    r = await client.post("/api/holidays", headers=_auth(token), json={
        "name": f"Fechas {uuid.uuid4().hex[:8]}",
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "expected_demand_factor": 3.0,
    })
    assert r.status_code == 201, r.text
    created = r.json()
    assert created["start_date"] == start.isoformat()
    assert created["end_date"] == end.isoformat()

    bad = await client.post("/api/holidays", headers=_auth(token), json={
        "name": f"Fechas {uuid.uuid4().hex[:8]}",
        "start_date": end.isoformat(),
        "end_date": start.isoformat(),
    })
    assert bad.status_code == 400
    assert "fin" in bad.json()["detail"].lower()


async def test_recommender_consumes_holiday_factor(client):
    token = await _login(client, "admin", "admin123")
    # ROS-001 has no seeded feast, so the holiday created here is its only
    # upcoming feast -> the configured factor deterministically joins the model.
    products = (await client.get("/api/products", headers=_auth(token))).json()
    target = next(p for p in products if p["code"] == "ROS-001")
    start = date.today() + timedelta(days=2)
    r = await client.post("/api/holidays", headers=_auth(token), json={
        "name": f"Factor Test {uuid.uuid4().hex[:8]}",
        "start_date": start.isoformat(),
        "end_date": start.isoformat(),
        "expected_demand_factor": 3.0,
        "product_ids": [target["id"]],
    })
    assert r.status_code == 201, r.text
    holiday_id = r.json()["id"]

    body = (await client.get("/api/ai/recomendaciones", headers=_auth(token))).json()
    item = next((i for i in body["items"] if i["code"] == "ROS-001"), None)
    assert item is not None, "ROS-001 with configured factor must be recommended"
    assert "factor de demanda esperada x3.0" in item["reason"]
    assert item["estimated_demand"] > 0

    await client.delete(f"/api/holidays/{holiday_id}", headers=_auth(token))