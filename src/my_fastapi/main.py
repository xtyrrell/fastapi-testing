import asyncio
from contextlib import asynccontextmanager
from typing import Annotated
import uuid

from fastapi import Depends, FastAPI
from sqlmodel import SQLModel, select

from .dependencies import (
    get_async_session,
    get_async_session_maker,
    initialise_async_engine,
    initialise_async_session_maker,
)
from .connection_from_docs import run_sync
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .models import Item


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting...")
    await initialise_async_engine()
    await initialise_async_session_maker()
    await run_sync(SQLModel.metadata.create_all)
    yield
    print("Shutting down...")


app = FastAPI(title="my_fastapi", lifespan=lifespan)


@app.get("/")
def index():
    return {"Hello": "World"}


@app.get("/items")
async def show_items(
    async_session_maker: Annotated[
        async_sessionmaker[AsyncSession], Depends(get_async_session_maker)
    ]
):
    async with async_session_maker() as session:
        res = await session.scalars(select(Item))
        return [item for item in res]


@app.post("/items")
async def create_item(
    item: Item,
    async_session_maker: Annotated[
        async_sessionmaker[AsyncSession], Depends(get_async_session_maker)
    ],
):
    async with async_session_maker() as session:
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item


@app.get("/injected-session")
async def get_injected_session(
    async_session: Annotated[AsyncSession, Depends(get_async_session)],
):
    print("my-fastapi: get_injected_session", async_session)

    id = uuid.uuid4()
    async_session.add(Item(id=id, name="injected item"))
    await async_session.commit()

    engine = async_session.get_bind()
    url = engine.engine.url

    db_info = {
        "database_url": str(url),
        "driver": url.drivername,
        "database": url.database,
        "host": url.host,
        "port": url.port,
        "username": url.username,
    }

    return db_info


@app.get("/db-connection")
async def get_db_connection(
    async_session_maker: Annotated[
        async_sessionmaker[AsyncSession], Depends(get_async_session_maker)
    ],
):
    async with async_session_maker() as session:
        engine = session.get_bind()
        url = engine.engine.url

    db_info = {
        "database_url": str(url),
        "driver": url.drivername,
        "database": url.database,
        "host": url.host,
        "port": url.port,
        "username": url.username,
    }

    return db_info


async def sleep_and_crash(seconds: int):
    await asyncio.sleep(seconds)
    raise Exception("Crash!")
