import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )

from psycopg_pool import AsyncConnectionPool

DB_URI = "postgresql://postgres:123456@127.0.0.1:5432/ainame"


async def main():

    print(type(asyncio.get_running_loop()))

    pool = AsyncConnectionPool(
        conninfo=DB_URI,
        open=False
    )

    await pool.open()

    print("连接成功")

    await pool.close()


asyncio.run(main())