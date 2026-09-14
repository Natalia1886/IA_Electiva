"""Pytest bootstrap — the suite runs against a DEDICATED test database.

The store database (`milan_db`, where the app lives) is never touched:
``DATABASE_URL`` is redirected to `milan_test` before any ``app.*`` import,
the database is created if missing, and the schema + demo data are seeded once
per session. This keeps tests reproducible and leaves the real store data
untouched (Prompt 20 constraint).
"""
import os
from urllib.parse import urlsplit, urlunsplit

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine

# 1) Point the application at the test database, BEFORE importing app modules.
_DEFAULT_URL = "postgresql+asyncpg://milan:milan123@localhost:5432/milan_db"
TEST_DATABASE_NAME = "milan_test"


def _test_database_url() -> str:
    url = os.getenv("DATABASE_URL", _DEFAULT_URL)
    return urlunsplit(urlsplit(url)._replace(path=f"/{TEST_DATABASE_NAME}"))


os.environ["DATABASE_URL"] = _test_database_url()

# 2) Force the mock extractor in tests: uploading a photo must never hit the
#    real (paid) vision provider, nor depend on the developer's .env key.
os.environ["OPENAI_API_KEY"] = ""

# 2) Only now import the application internals (they build the engine from the env).
from app.database import Base, engine  # noqa: E402
from app.seed import seed  # noqa: E402


async def _ensure_test_database_exists() -> None:
    """CREATE DATABASE milan_test if it does not exist yet."""
    admin_url = urlunsplit(urlsplit(_test_database_url())._replace(path="/milan_db"))
    admin = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    async with admin.connect() as conn:
        exists = await conn.scalar(
            sa.text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": TEST_DATABASE_NAME},
        )
        if not exists:
            await conn.execute(sa.text(f'CREATE DATABASE "{TEST_DATABASE_NAME}"'))
    await admin.dispose()


@pytest.fixture(scope="session", autouse=True)
async def _test_db():
    await _ensure_test_database_exists()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await seed()  # schema (create_all) + admin/seller + products + holidays + 400d history
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)