from typing import AsyncGenerator
import pytest
from fastapi.testclient import TestClient
import pytest_asyncio

from sqlalchemy import NullPool, StaticPool, text
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine


from . import settings
from .dependencies import get_async_session

from .main import app

# The following forces all tests to use the session event loop.
# ---
# import pytest

# from pytest_asyncio import is_async_test


# def pytest_collection_modifyitems(items):
#     pytest_asyncio_tests = (item for item in items if is_async_test(item))
#     session_scope_marker = pytest.mark.asyncio(loop_scope="session")
#     for async_test in pytest_asyncio_tests:
#         async_test.add_marker(session_scope_marker, append=False)
# ---

# MAX TODO NEXT:
# try see if I can reproduce the issue from seadotdev-base tests here
# by using a fixture to replace the async session and
# using TestClient in a new test.
# FIRST set up fixtures / tests as per https://medium.com/@navinsharma9376319931/mastering-fastapi-crud-operations-with-async-sqlalchemy-and-postgresql-3189a28d06a2
# and / or https://praciano.com.br/fastapi-and-async-sqlalchemy-20-with-pytest-done-right.html
# ACTUALLY USING https://docs.sqlalchemy.org/en/20/_modules/examples/asyncio/greenlet_orm.html


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def async_engine() -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine(
        settings.DATABASE_URL_ASYNC,
        # poolclass=StaticPool,
        echo=True,
    )

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture(scope="function", loop_scope="session")
async def async_session(
    async_engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(async_engine) as session:
        async with session.begin():
            await session.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS item (id SERIAL PRIMARY KEY, name TEXT)"
                )
            )
            yield session
            await session.rollback()


@pytest_asyncio.fixture(scope="function", loop_scope="session")
async def client(async_session: AsyncSession):
    async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
        yield async_session

    app.dependency_overrides[get_async_session] = override_get_async_session

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
