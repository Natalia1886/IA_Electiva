# Backend — Milán (Inventory & Sales)

FastAPI backend for the Milán religious-goods store system: REST API, PostgreSQL
(async SQLAlchemy 2.0), JWT + bcrypt authentication, centralized error handling
and the AI modules (digitizer, recommendations) wired through service layers.

## Requirements

- Python 3.11
- PostgreSQL 16 (via Docker Compose at the repo root) running on `localhost:5432`

## Installation

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment variables

Copy the reference file and adjust the values, especially `SECRET_KEY`:

```bash
cp .env.example .env
```

| Variable | Description | Required |
| --- | --- | --- |
| `DATABASE_URL` | Async PostgreSQL connection string (`postgresql+asyncpg://user:pass@host:port/db`) | Yes |
| `SECRET_KEY` | Random secret used to sign JWTs | Yes |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT lifetime in minutes (default `480`) | No |
| `OPENAI_API_KEY` | API key for the generative explainer (set when the LLM provider is enabled) | No |
| `CORS_ORIGINS` | Comma-separated allowed origins (default `http://localhost:5173,http://127.0.0.1:5173`) | No |

Credentials and connection strings are **never** hardcoded: everything loads from
the environment / `.env` through `app/config.py` (pydantic-settings).

## Project structure

```
backend/
├── app/
│   ├── main.py            # app factory, lifespan (create_all), middleware, routers
│   ├── config.py          # pydantic-settings, reads .env
│   ├── database.py        # async engine + session factory + Base
│   ├── seed.py            # idempotent demo-data seeder
│   ├── core/
│   │   ├── security.py    # JWT + bcrypt helpers
│   │   ├── permissions.py # role↔permission matrix (declarative)
│   │   ├── exceptions.py  # MilanError hierarchy (all domain errors)
│   │   └── errors.py      # centralized exception handlers (registered in main.py)
│   ├── api/
│   │   ├── deps.py        # auth (get_current_user) + authorization (require_role / require_permission)
│   │   └── routes/        # one module per resource (auth, users, categories, ...)
│   ├── models/            # SQLAlchemy async models
│   ├── schemas/           # Pydantic schemas (request/response)
│   └── services/          # business logic (sales, inventory, summaries, AI)
├── tests/test_api.py      # integration tests against a seeded DB
├── pytest.ini
├── requirements.txt
└── .env.example
```

## Run

With Postgres up (from the repo root):

```bash
docker compose up -d
```

Start the API (from `backend/`):

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Seed demo data (idempotent — safe to re-run):

```bash
.venv/bin/python -m app.seed
```

Interactive docs: <http://127.0.0.1:8000/docs>

Health check: <http://127.0.0.1:8000/api/health>

## Tests

```bash
# Postgres must be up and seeded
.venv/bin/python -m pytest tests -q
```

## Error handling

All responses are uniform JSON. Handlers live in `app/core/errors.py` and are
registered once in `app/main.py`:

- Application errors → `{"detail": msg, "code"?, "details"?}` with their HTTP status
- Request validation → `422` with the field-error list
- DB integrity conflicts (duplicate keys / FK) → `409`
- Anything unexpected → `500 {"detail": "Error interno del servidor"}` (traceback logged)

Domain code raises custom exceptions from `app/core/exceptions.py`
(`NotFoundError`, `ConflictError`, `BadRequestError`, `UnauthorizedError`,
`ForbiddenError`, `ServiceUnavailableError`) instead of throwing ad-hoc errors.