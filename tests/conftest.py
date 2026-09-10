import sys
import os
from pathlib import Path
import pytest
import pytest_asyncio
import fakeredis.aioredis
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Flag testing environment BEFORE main imports
os.environ["TESTING"] = "1"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app, limiter
from app.dependencies import get_db, get_redis, set_redis_client
from app.models import Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(autouse=True)
def disable_limiter():
    limiter.enabled = True
    yield
    limiter.enabled = True


@pytest_asyncio.fixture(scope="function")
async def db_session():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    # FakeRedis instance created strictly inside test's event loop
    fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    set_redis_client(fake_redis)

    async def _override_get_db():
        yield db_session

    async def _override_get_redis():
        yield fake_redis

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_redis] = _override_get_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    await fake_redis.flushdb()
    await fake_redis.aclose()
