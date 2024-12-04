# import json
from collections.abc import AsyncGenerator
from typing import Any

from pydantic import json as pydantic_json
from sqlalchemy import create_engine, StaticPool, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)

from . import settings


# # Override the SQLAlchemy JSON serializer to process Pydantic objects in object fields, e.g. Address
# def pydantic_json_serializer(*args: Any, **kwargs: Any) -> str:
#     """
#     Encodes json in the same way that pydantic does.
#     """
#     return json.dumps(*args, default=pydantic_json.pydantic_encoder, **kwargs)

_async_engine: AsyncEngine | None = None
_async_sessionmaker: async_sessionmaker | None = None


# This is a function so that we can only call create_async_engine
# within FastAPI's lifecycle manager; which may be needed (assuming create_async_engine
# uses the current event loop) as per
# https://fastapi.tiangolo.com/advanced/async-tests/#other-asynchronous-function-calls
async def initialise_async_engine():
    global _async_engine
    global _async_sessionmaker
    if _async_engine is None:
        _async_engine = create_async_engine(
            settings.DATABASE_URL_ASYNC,
            poolclass=StaticPool,
            # json_serializer=pydantic_json_serializer,
            # pool_pre_ping=True,
            # pool_size=4,  # Number of connections to keep open in the pool
            # max_overflow=4,  # Number of connections that can be opened beyond the pool_size
            # pool_recycle=3600,  # Recycle connections after 1 hour
            # pool_timeout=120,  # Raise an exception after 2 minutes if no connection is available from the pool
        )
        _async_sessionmaker = async_sessionmaker(
            bind=_async_engine, expire_on_commit=False
        )
        return _async_engine


# Async session generator
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    if _async_engine is None or _async_sessionmaker is None:
        raise Exception("Async engine and/or sessionmaker not initialized")

    session = _async_sessionmaker()
    if session is None:
        raise Exception("Database Session could not be initialized")

    try:
        yield session
    finally:
        await session.close()
