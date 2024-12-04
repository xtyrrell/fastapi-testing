import asyncio
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlmodel import SQLModel, select

from .dependencies import get_async_session, initialise_async_engine
from .connection_from_docs import run_sync
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from .models import Item


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting...")
    engine = await initialise_async_engine()
    # This fails with a sqlalchemy.exc.MissingGreenlet error...
    # SQLModel.metadata.create_all(engine.sync_engine)
    await run_sync(SQLModel.metadata.create_all)
    yield
    print("Shutting down...")


app = FastAPI(lifespan=lifespan)


@app.get("/")
def index():
    return {"Hello": "World"}


@app.get("/items")
async def show_items(async_session: AsyncSession = Depends(get_async_session)):
    res = await async_session.scalars(select(Item))
    return [item for item in res]


@app.post("/items")
async def create_item(
    item: Item, async_session: AsyncSession = Depends(get_async_session)
):
    async_session.add(item)
    await async_session.commit()
    await async_session.refresh(item)
    return item


@app.get("/db-connection")
async def get_db_connection(db_session: AsyncSession = Depends(get_async_session)):
    engine = db_session.get_bind()
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
