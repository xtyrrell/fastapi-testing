from typing import AsyncGenerator, Generator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

from .dependencies import get_async_session_maker
from .main import app

from . import settings


# TODO: MAX: Probably use this to do the general database prep stuff like migrations etc
# @pytest.fixture(scope="session", autouse=True)
# def setup_test_db(setup_db: Generator) -> Generator:
#     engine = create_engine(
#         f"{settings.DATABASE_URL_ASYNC.replace('+asyncpg', '')}/test"
#     )

#     with engine.begin():
#         Base.metadata.drop_all(engine)
#         Base.metadata.create_all(engine)
#         yield
#         Base.metadata.drop_all(engine)

#     engine.dispose()


@pytest.fixture
async def async_session_maker() -> (
    AsyncGenerator[async_sessionmaker[AsyncSession], None]
):
    # https://github.com/sqlalchemy/sqlalchemy/issues/5811#issuecomment-756269881
    async_engine = create_async_engine(settings.DATABASE_URL_ASYNC)
    async with async_engine.connect() as conn:
        await conn.begin()
        await conn.begin_nested()
        _async_sessionmaker = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=conn,
            future=True,
        )

        # @event.listens_for(_async_sessionmaker.sync_session, "after_transaction_end")
        # def end_savepoint(session: Session, transaction: SessionTransaction) -> None:
        #     if conn.closed:
        #         return
        #     if not conn.in_nested_transaction():
        #         if conn.sync_connection:
        #             conn.sync_connection.begin_nested()

        yield _async_sessionmaker
        await conn.rollback()

    await async_engine.dispose()


@pytest.fixture
async def async_session(
    async_session_maker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


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
