import asyncio

from sqlalchemy import func, text
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


async def test_injected_session(
    ac: AsyncClient, async_session_maker: async_sessionmaker[AsyncSession]
):
    response = await ac.get("/injected-session")
    assert response.status_code == 200
    assert response.json()["database"] == "postgres"

    async with async_session_maker() as async_session:
        res = await async_session.scalars(
            select(Item).where(Item.name == "injected item")
        )
        items = res.all()
        assert len(items) == 1
        assert items[0].name == "injected item"
