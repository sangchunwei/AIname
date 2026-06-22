import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )

from psycopg_pool import AsyncConnectionPool
import settings


async def main():

    print(type(asyncio.get_running_loop()))

    pool = AsyncConnectionPool(
        conninfo=settings.POSTGRES_CHECKPOINT_DB_URI,
        open=False
    )

    await pool.open()

    print("连接成功")

    await pool.close()


asyncio.run(main())
