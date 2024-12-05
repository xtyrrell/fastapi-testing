from typing import AsyncGenerator, Generator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.pool import AssertionPool
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

from .models import Base

from .dependencies import get_async_session_maker
from .main import app

from . import settings


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    engine = create_engine(f"{settings.DATABASE_URL_ASYNC.replace('+asyncpg', '')}")

    with engine.begin():
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        yield
        Base.metadata.drop_all(engine)

    engine.dispose()


@pytest.fixture
async def async_session_maker() -> (
    AsyncGenerator[async_sessionmaker[AsyncSession], None]
):
    # https://github.com/sqlalchemy/sqlalchemy/issues/5811#issuecomment-756269881
    async_engine = create_async_engine(
        settings.DATABASE_URL_ASYNC, poolclass=AssertionPool
    )
    async with async_engine.connect() as conn:
        await conn.begin()
        await conn.begin_nested()

        async_session_maker = async_sessionmaker(expire_on_commit=False, bind=conn)

        yield async_session_maker

        await conn.rollback()

    await async_engine.dispose()


@pytest.fixture
async def async_session(
    async_session_maker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        return session


@pytest.fixture
async def ac(
    async_session_maker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncClient, None]:
    # Overriding the get_async_session_maker dependency is all we need
    # to do because the async_session uses the async_session_maker and
    # will therefore also connect to the test DB.
    def overridden_get_async_session_maker() -> Generator:
        yield async_session_maker

    app.dependency_overrides[get_async_session_maker] = (
        overridden_get_async_session_maker
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
