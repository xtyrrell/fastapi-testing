# import json
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)

from . import settings


global_async_engine: AsyncEngine | None = None
global_async_sessionmaker: async_sessionmaker | None = None


# We initialise the async engine and async session maker once and
# reuse them per request.
# This saves us from creating a new connection for each request.
async def initialise_async_engine():
    global global_async_engine
    global_async_engine = create_async_engine(
        settings.DATABASE_URL_ASYNC,
        echo=True,
    )
    return global_async_engine


async def initialise_async_session_maker() -> async_sessionmaker[AsyncSession]:
    global global_async_sessionmaker
    global_async_sessionmaker = async_sessionmaker(
        bind=global_async_engine, expire_on_commit=False
    )
    return global_async_sessionmaker


async def get_async_session_maker() -> (
    AsyncGenerator[async_sessionmaker[AsyncSession], None]
):
    if global_async_sessionmaker is None:
        raise Exception("Async engine and/or sessionmaker not initialized")
    yield global_async_sessionmaker


async def get_async_session(
    async_session_maker: Annotated[
        async_sessionmaker[AsyncSession], Depends(get_async_session_maker)
    ],
) -> AsyncGenerator[AsyncSession, None]:
    """A simple convenience to get an async session."""
    async with async_session_maker() as session:
        yield session
