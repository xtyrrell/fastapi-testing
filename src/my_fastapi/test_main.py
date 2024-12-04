import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from httpx import AsyncClient
from sqlmodel import select

from .models import Item


async def test_index(ac: AsyncClient):
    response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}


async def test_db_connection_database(ac: AsyncClient):
    response = await ac.get("/db-connection")
    assert response.json()["database"] == "postgres"


async def test_async_session_maker(
    async_session_maker: async_sessionmaker[AsyncSession],
):
    assert async_session_maker is not None

    async with async_session_maker() as session:
        res = await session.execute(text("SELECT VERSION()"))
        assert res.one()[0].startswith("PostgreSQL")


async def test_create_item(
    ac: AsyncClient, async_session_maker: async_sessionmaker[AsyncSession]
):
    await asyncio.sleep(1)
    response = await ac.post(
        "/items", json={"id": "10000000-0000-4000-9000-000000000000", "name": "test"}
    )
    print("response", response.json())
    assert response.status_code == 200
    assert response.json() == {
        "id": "10000000-0000-4000-9000-000000000000",
        "name": "test",
    }

    async with async_session_maker() as session:
        res = await session.scalar(
            select(Item).where(Item.id == "10000000-0000-4000-9000-000000000000")
        )
        assert res is not None
        assert res.name == "test"


# From
# https://pytest-asyncio.readthedocs.io/en/latest/how-to-guides/run_session_tests_in_same_loop.html
# This ensures that all tests in the session use the same event loop.
# We can probably clean this up by: removing this modifier hook and removing all the loop_scope="session" markers
# and trying to set the loop to the correct scope in general.
