"""Pytest fixtures for MH-CyberScore backend tests."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_current_user, get_db, UserClaims
from app.database import Base
from app.main import app

# Use SQLite async for tests (no PostgreSQL required)
TEST_DATABASE_URL = "sqlite+aiosqlite:///file::memory:?cache=shared&uri=true"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(autouse=True)
async def setup_db() -> AsyncGenerator[None, None]:
    """Create all tables before each test, drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a test database session."""
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
def mock_user() -> UserClaims:
    """Return a mock admin user for auth-protected endpoints."""
    return UserClaims(
        sub="test-user-id",
        email="admin@malakoffhumanis.com",
        name="Test Admin",
        role="admin",
    )


@pytest.fixture
async def client(
    db_session: AsyncSession,
    mock_user: UserClaims,
) -> AsyncGenerator[AsyncClient, None]:
    """Yield an authenticated httpx AsyncClient for testing.

    Overrides the DB and auth dependencies so tests do not require
    a real PostgreSQL or Keycloak instance.
    """

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    async def override_get_current_user() -> UserClaims:
        return mock_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
