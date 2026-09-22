import asyncio
import os
import sys
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from fastapi import Depends

# psycopg async requires SelectorEventLoop on Windows (not ProactorEventLoop).
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Force the test database URL so tests NEVER touch the development DB.
TEST_DATABASE_URL = "postgresql+psycopg://mausam:mausam_dev_password@localhost:5433/mausam_mitra_test"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault(
    "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
)
os.environ.setdefault("APP_ENV", "test")

from app.db.session import get_db
from app.main import app

engine = create_async_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)


@pytest_asyncio.fixture(scope="session")
async def prepare_database() -> AsyncGenerator[None, None]:
    """Require a running PostGIS instance (docker compose up -d) and apply migrations to the test DB."""
    async with engine.begin() as conn:
        await conn.execute(
            __import__("sqlalchemy").text("SELECT PostGIS_Version()")
        )
    
    # Apply Alembic migrations to the test database
    import alembic.config
    import alembic.command
    from pathlib import Path
    
    backend_dir = Path(__file__).resolve().parent.parent
    alembic_ini_path = backend_dir / "alembic.ini"
    
    alembic_cfg = alembic.config.Config(str(alembic_ini_path))
    alembic_cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    alembic_cfg.set_main_option("script_location", str(backend_dir / "alembic"))
    alembic.command.upgrade(alembic_cfg, "head")
    
    yield
    await engine.dispose()

@pytest_asyncio.fixture(autouse=True)
async def isolate_tests(prepare_database: None) -> AsyncGenerator[None, None]:
    """Ensure each test runs on a clean slate by truncating all application tables."""
    from app.db import Base
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            # Only truncate our application tables, not PostGIS internals
            if table.name != "spatial_ref_sys":
                await conn.execute(__import__("sqlalchemy").text(f'TRUNCATE TABLE {table.name} CASCADE'))
    yield


@pytest_asyncio.fixture
async def db_session(
    prepare_database: None,
) -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(
    prepare_database: None,
) -> AsyncGenerator[AsyncClient, None]:
    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with TestSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()

    async def _override_get_current_user(db: AsyncSession = Depends(_override_get_db)):
        from sqlalchemy import select
        from app.models.user import User
        from app.core.enums import Role
        import uuid
        
        user = await db.scalar(select(User).where(User.email == "admin@example.com"))
        if not user:
            user = User(
                id=uuid.uuid4(),
                email="admin@example.com",
                full_name="Admin",
                password_hash="fake",
                role=Role.ADMIN,
                is_active=True
            )
            db.add(user)
            await db.commit()
        return user

    from app.api.deps import get_current_user, get_db
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
