from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient
from sqlalchemy import select

from .models import Item


async def test_index(ac: AsyncClient):
    response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}


async def test_db_connection_database(ac: AsyncClient):
    response = await ac.get("/db-connection")
    assert response.json()["database"] == "postgres"


async def test_async_session_maker(
    async_session: AsyncSession,
):
    assert async_session is not None

    res = await async_session.execute(text("SELECT VERSION()"))
    assert res.one()[0].startswith("PostgreSQL")


async def test_create_item(ac: AsyncClient, async_session: AsyncSession):
    response = await ac.post(
        "/items", json={"id": "10000000-0000-4000-9000-000000000000", "name": "test"}
    )
    print("response", response.json())
    assert response.status_code == 200
    assert response.json() == {
        "id": "10000000-0000-4000-9000-000000000000",
        "name": "test",
    }

    res = await async_session.scalar(
        select(Item).where(Item.id == "10000000-0000-4000-9000-000000000000")
    )
    assert res is not None
    assert res.name == "test"


async def test_injected_session(ac: AsyncClient, async_session: AsyncSession):
    response = await ac.get("/injected-session")
    assert response.status_code == 200
    assert response.json()["name"] == "injected item"

    res = await async_session.scalars(select(Item).where(Item.name == "injected item"))
    items = res.all()
    assert len(items) == 1
    assert items[0].name == "injected item"
