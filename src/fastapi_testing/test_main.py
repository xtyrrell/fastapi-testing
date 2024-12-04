import asyncio
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .main import app


# def test_index():
#     client = TestClient(app)

#     response = client.get("/")
#     assert response.status_code == 200
#     assert response.json() == {"Hello": "World"}


# def test_db_connection_code(client: TestClient):
#     response = client.get("/db-connection")
#     assert response.status_code == 200
#     assert response.json()["database"] == "postgres"


# def test_db_connection_database(client: TestClient):
#     response = client.get("/db-connection")
#     assert response.json()["database"] == "postgres"


@pytest.mark.asyncio(loop_scope="session")
async def test_async_session(async_session: AsyncSession):
    assert async_session is not None

    res = await async_session.execute(text("SELECT VERSION()"))
    assert res.rowcount == 1
    assert res.first()[0].startswith("PostgreSQL")


@pytest.mark.asyncio(loop_scope="session")
async def test_create_item(client: TestClient):
    await asyncio.sleep(1)
    response = client.post(
        "/items", json={"id": "10000000-0000-4000-9000-000000000000", "name": "test"}
    )
    print(response.json())
    assert response.status_code == 200
    assert response.json() == {
        "id": "10000000-0000-4000-9000-000000000000",
        "name": "test",
    }


# From
# https://pytest-asyncio.readthedocs.io/en/latest/how-to-guides/run_session_tests_in_same_loop.html
# This ensures that all tests in the session use the same event loop.
# We can probably clean this up by: removing this modifier hook and removing all the loop_scope="session" markers
# and trying to set the loop to the correct scope in general.
