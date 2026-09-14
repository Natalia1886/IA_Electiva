# Milan — Inventory Management System for a Religious Goods Store

A web application to digitize and optimize inventory and sales management for a
religious goods store (statues of the Virgin Mary, saints, candles, nativity
scenes), using generative AI to accelerate digitization and analysis.

## Architecture

| Layer     | Technology                                   |
|-----------|----------------------------------------------|
| Frontend  | React 18 + Vite + TypeScript                 |
| Backend   | Python 3.11 + FastAPI + SQLAlchemy 2 (async) |
| Database  | PostgreSQL 16 (Docker)                      |
| Auth      | JWT (Bearer) + bcrypt, roles: `admin` / `salesperson` |
| AI digitizer | Photo upload → vision model (OpenAI) / silent mock fallback, operator-approved reviews confirm via `POST /sales` |
| AI recommendations | scikit-learn segmentation model over digitized history → quantity logic → LLM phrasing (template fallback) |

```
milan12/
├── docker-compose.yml        # PostgreSQL 16
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI entrypoint (mounts routers, creates tables, registers error handlers)
│   │   ├── config.py         # Settings (.env)
│   │   ├── database.py       # Async engine + session
│   │   ├── core/             # security (JWT/bcrypt), permissions (role matrix), stock_status (pure rule), exceptions, error handlers
│   │   ├── models/           # User, Product/Category, ReligiousHoliday, Sale/Item, StockMovement, DigitizationRecord
│   │   ├── schemas/          # Pydantic v2 request/response models
│   │   ├── api/deps.py       # auth (get_current_user) + authorization (require_role/require_permission)
│   │   ├── api/routes/       # auth, users, categories, holidays, products, sales, inventory, reports, ai_*
│   │   ├── services/         # products, sales, inventory, daily_summary, ai/ (holiday_engine, vision, digitizer, segmentation, recommendations, natural_language)
│   │   ├── ai_models/        # trained segmentation artifacts (scripts/train_segmenter.py)
│   │   ├── scripts/          # training script (feature engineering + metrics)
│   │   └── seed.py           # Demo data (admin/admin123, vendedor/vendedor123)
│   └── tests/                # Integration tests (48) — pytest + httpx
│   └── README.md             # Backend local-launch guide + env vars
└── frontend/
    └── src/
        ├── api/              # fetch client + types
        ├── auth/             # AuthContext (JWT)
        ├── components/       # Layout, RequireAuth
        └── pages/            # Login, Dashboard, Sales, DailySummary, Products, Inventory, Users, Digitizer, Recommendations
```

## Running

Requires Docker (PostgreSQL) and Python 3.11.

```bash
# 1. Database
docker compose up -d

# 2. Backend
cd backend
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env            # edit if needed
.venv/bin/python -m app.seed     # creates schema + demo data
.venv/bin/uvicorn app.main:app --reload --port 8000
# docs: http://127.0.0.1:8000/docs

# 3. Frontend
cd frontend
npm install
npm run dev                     # http://localhost:5173 (proxies /api → :8000)
```

Demo users: `admin / admin123` (Administrator) · `vendedor / vendedor123` (Salesperson)

## Permissions

| Area | admin | salesperson |
|------|:-----:|:-----------:|
| Auth (login/me) | ✓ | ✓ |
| Products & categories (view) | ✓ | ✓ |
| Products & categories (create/edit/delete) | ✓ | ✗ |
| Sales (record/view) | ✓ | ✓ |
| Daily summary | ✓ | ✓ |
| Inventory (current stock status) | ✓ | ✓ |
| Inventory (purchase alerts) | ✓ | ✗ |
| Inventory movements (in/out/history) | ✓ | ✗ |
| Admin dashboard & reports | ✓ | ✗ |
| AI digitizer | ✓ | ✓ |
| AI purchase recommendations | ✓ | ✗ |
| User management | ✓ | ✗ |

## Frontend routes (by role)

Navigation is **generated per role**: the sidebar only renders entries allowed for the current
user's role, so a salesperson's DOM never contains the Users or Recommendations links.

| Route | Screen | admin | salesperson |
|-------|--------|:-----:|:-----------:|
| `/login` | Login | ✓ | ✓ |
| `/dashboard` | Panel administrativo | ✓ | ✗ |
| `/home` | Mi día (daily-use dashboard) | ✗ | ✓ |
| `/sales` | Ventas | ✓ | ✓ |
| `/summary` | Resumen diario | ✓ | ✓ |
| `/products` | Productos | ✓ | ✓ |
| `/inventory` | Inventario (limited view for salesperson) | ✓ | ✓ |
| `/digitizer` | Digitalizador AI | ✓ | ✓ |
| `/recommendations` | Recomendaciones de compra | ✓ | ✗ |
| `/holidays` | Festividades religiosas (CRUD) | ✓ | ✗ |
| `/users` | Usuarios | ✓ | ✗ |
| `/profile` | Mi perfil | ✓ | ✓ |
| any other | Redirects to role home (`/dashboard` admin, `/home` salesperson) | — | — |

Role guards are enforced at the route level (`RequireAuth role="admin"`) **and** at the navigation
level (role-filtered `NAV_ITEMS` in `Layout.tsx`), so a restricted screen is unreachable and unlinked
for the salesperson.

Permission enforcement is **declarative and centralized**: `app/core/permissions.py`
holds the role↔permission matrix; `require_role("admin")` / `require_permission("inventory:view:alerts")`
dependencies in `app/api/deps.py` gate every route. The salesperson's inventory
access is explicitly limited to `inventory:view:limited` (current stock only).

## Data model

- **users** — admins and salespeople
- **categories**, **products** — catalog with price, cost, stock, `min_stock`, `is_active` (soft delete)
- **religious_holidays** + **product_holidays** — fixed and variable feasts (Easter/Corpus Christi computed via the holiday engine) linked to products
- **sales**, **sale_items** — fiscal sales (payment method cash/card/transfer) with auto stock deduction (transactional); digitized (notebook) sales are stored via the same `POST /sales` with `digitization_id` but are **historical**: they never touch current stock nor log a movement
- **stock_movements** — signed in/out log (purchase, sale, adjustment, return) with idempotency by sale
- **digitization_records** — photo uploads, extracted JSON (`raw_data`), analyzer + page date, review state, `correction_stats` (detected vs confirmed accuracy over time), imported-sale provenance

## Core behaviors implemented

1. **Auth**: JWT login (bcrypt-hashed passwords); declarative role/permission gates
   (`require_role("admin")`, `require_permission(...)`) enforcing the matrix on every route.
2. **Products CRUD**: paginated admin table with server-side search (name/code), category and low-stock
   filters, create/edit modal with client-side validation (non-negative price/stock, required fields — the
   backend re-validates too), and deactivation/re-activation shown explicitly as a non-destructive soft delete
   (salespeople keep read-only access).
3. **Sales**: cart screen (product search, quantities capped at available stock client-side and re-checked
   server-side, live line subtotals and grand total, payment method — cash/card/transfer — with confirmation
   and post-sale modals). Stock deduction and movement log are committed in the **same atomic transaction** as
   the sale (row-locked product fetch prevents overselling; any failure — e.g. insufficient stock or empty
   details — rolls back everything).
4. **Daily summary**: per-day value, transactions, units, per-product breakdown, top movers.
5. **Inventory**: current stock per product with the **three-level status** (Normal / Low / Out of Stock) computed
   live from `stock` vs `min_stock` by the pure `compute_stock_status` function (`app/core/stock_status.py`) — never
   stored. Alerts list covers Low + Out of Stock (admin-only), signed movements history (purchase/adjustment/return)
   with filters, and admin-only manual entries that record a `stock_movements` row in the same transaction.
6. **Admin dashboard**: KPIs (today's revenue, transactions, units sold), stock status counts (low /
   out-of-stock), 7-day sales chart, top products (30d), stock alerts table, and a summary of purchase
   recommendations — all composed from real endpoints (`/reports/dashboard`, `/inventory`, `/ai/recommendations`).
7. **AI digitizer** (full flow): upload a photo of the notebook (validated image, optional page date) → the vision model
   (`OpenAIVisionExtractor`) proposes date/code/quantity/price per row following a **never-invent contract** (unreadable
   fields stay empty and flagged; a silent `MockExtractor` is used when no API key is set) → the operator reviews an
   editable pre-filled table (unknown catalog codes flagged, page-date substitution flagged) → rows are grouped by date
   and confirmed through the normal `POST /sales` with `digitization_id` (historical: no stock/movement impact, reviewed
   `unit_price` allowed). The dedicated `/ai/digitize/import` route was removed. Every batch stores `correction_stats`
   comparing extracted vs confirmed values, so extraction accuracy is tracked over time.
8. **AI recommendations** (`GET /ai/recomendaciones`, admin-only): the trained `KMeans` segmentation over digitized sales
    history (sales frequency, days since last sale, sales variance, category, holiday correlation) classifies each product;
    a rule layer cross-references the segment, inventory, `min_stock` and the next 60 days of religious feasts to compute
    `estimated_demand` and `suggested_quantity`; each item includes an explainable `reason` built from the actual feature
    values, and `rationale` phrases the decision the same way an LLM would (a real LLM rephrases only when `OPENAI_API_KEY`
    is set; otherwise a deterministic template built from the same numbers). The model is **the decider** — see
    `scripts/train_segmenter.py` for the training script that prints evaluation metrics (silhouette, Davies-Bouldin,
    inertia, cluster sizes) and saves the artifacts.
 9. **Religious holidays** (`/holidays`, admin-only CRUD): the administrator registers a feast with a fixed
    day/month, a variable date (Easter/Corpus) and/or an explicit season start/end, links it to **multiple products**
    (M2M via `product_holidays`) and sets an **expected demand factor** (1.x multiplier; presets low 1.2 / medium 1.5 /
    high 2.0, freely editable). The recommender reads `expected_demand_factor` straight from the database and blends it
    with the historical uplift — when the configured factor exceeds the observed one, it dominates both `estimated_demand`
    and the explanation (e.g. `factor de demanda esperada x3.0 registrado por el administrador`). Soft delete
    (`is_active`) so historical links survive. Screen: `src/pages/Holidays.tsx` (table + modal form, Products pattern).

## ML pipeline (recommender)

```bash
cd backend
.venv/bin/python -m app.seed              # demo sales history (incl. holiday demand bursts)
.venv/bin/python -m scripts.train_segmenter   # features + KMeans + metrics → app/ai_models/segmenter.joblib
curl http://127.0.0.1:8000/api/ai/recomendaciones -H "Authorization: Bearer <admin token>"
```

Example output (2026-09, seeded demo):

```
Upcoming holiday: San Judas Tadeo
Product: San Judas Tadeo 20 cm
Current stock: 3          Estimated demand: 47
Recommended quantity: 45 units
Reason: stock below minimum + 238% historical uplift around San Judas Tadeo
```

## Roadmap (incremental, per the course plan)

- Stage 2 (P16) — vision model connected to the digitizer (proposals only; operator confirms).
- Stage 3 (P17) — holiday analysis and the full recommendation pipeline.
- Stage 4 (P17) — team-trained scikit-learn segmentation model predicting demand and quantities.
- Stage 5 (P18) — holidays become a first-class resource: admin CRUD with multi-product links and
  an expected-demand factor consumed directly by the recommender.
- Stage 6 — the LLM explains/rephrases the model's recommendations (never decides); report polish remains.

## Tests (Prompt 20)

The suite runs against a **dedicated test database** (`milan_test`), never the
store database: `tests/conftest.py` redirects `DATABASE_URL` to `milan_test`,
creates it if missing, then drops/creates/seeds the schema once per session.
The real store DB (`milan_db`) is never touched, and `tests/test_critical_flows.py`
holds the end-to-end flows (positive + mandatory negative cases).

```bash
cd backend
.venv/bin/python -m pytest tests -q    # Postgres must be up (docker compose); no seed required
```

| Module | Case | Steps | Expected result |
|---|---|---|---|
| Login/roles | Admin login | POST `/auth/login` admin, GET `/auth/me` | 200, token; `role=admin` |
| Login/roles | Wrong password | POST `/auth/login` with bad password | **401** |
| Login/roles | Anonymous request | GET `/products`, `/ai/recomendaciones` without token | **401** |
| Login/roles | Salesperson on admin endpoints | GET `/users`, GET+POST `/holidays`, POST/PATCH/DELETE `/products`, GET `/ai/recomendaciones`, GET `/reports/dashboard` | **403 on all** |
| Product CRUD | Round trip | POST → PATCH → GET → DELETE → reactivate | 201/200/200/204/200 |
| Sales | Stock deduction | POST `/sales` qty 4 of a product; read stock, movements, history | 201; stock −4; `sale` movement (−4) linked to sale; present in history |
| Sales | **Insufficient stock (negative)** | POST `/sales` qty 6 against product with stock 5 | **400**, stock stays 5, no sale movement |
| Inventory | Alerts | Product stock 0 (min 1) and stock 2 (min 2); GET `/inventory/alerts` | Both present: `out_of_stock` and `low` |
| AI digitizer | Upload / incomplete detection | POST `/ai/digitize` image; confirm with `items: []`; confirm with unknown `digitization_id` | 201 `awaiting_review` (0 entries = nothing invented); **422** empty items; **400** unknown record |
| AI digitizer | Field not detected (unit) | `vision._sanitize_row` with `quantity:"abc"`, missing quantity, bad date | `quantity:None` + `quantity:ilegible`; no flag when field absent; `date:formato_invalido` |
| Recommendations | Admin-only + explainable | GET `/ai/recomendaciones` as admin / salesperson | 200 admin (non-empty, each `reason` derived from real features); **403** salesperson |
| Recommendations | Factor consumed | Holiday factor 3.0 (start +2d) linked to a product; GET `/ai/recomendaciones` | Item included; reason contains `factor de demanda esperada x3.0` |

## Project status

Prompts 1–20 complete: full-stack MVP with core CRUD, sales, inventory, reporting,
the AI digitizer (vision + operator review) and the ML-based purchase recommender
(segmentation model + explainable reasons + NL phrasing) working end-to-end,
verified by a 64-test suite that runs against an isolated test database.