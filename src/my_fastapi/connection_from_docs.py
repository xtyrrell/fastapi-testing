from sqlalchemy.ext.asyncio import create_async_engine

from . import settings


async def run_sync(x):
    # engine is an instance of AsyncEngine
    engine = create_async_engine(
        settings.DATABASE_URL_ASYNC,
        echo=True,
    )

    # conn is an instance of AsyncConnection
    async with engine.begin() as conn:
        # to support SQLAlchemy DDL methods as well as legacy functions, the
        # AsyncConnection.run_sync() awaitable method will pass a "sync"
        # version of the AsyncConnection object to any synchronous method,
        # where synchronous IO calls will be transparently translated for
        # await.
        await conn.run_sync(x)
