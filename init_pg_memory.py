# Windows 系统在使用 psycopg 异步连接时，必须切换事件循环策略。
# 避免 FastAPI 的事件循环与建表任务发生冲突
# 编写创建数据表脚本
import asyncio
import sys
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
import settings


async def setup_memory_db():

    print("正在连接 PostgreSQL...")
    async with AsyncPostgresSaver.from_conn_string(settings.POSTGRES_CHECKPOINT_DB_URI) as saver:
        await saver.setup()#在调用 setup() 方法时，会自动创建四张表来支撑 LangGraph 的检查点（Checkpoint）持久化机制
        print("✅ PostgreSQL 记忆持久化数据表创建成功！")
if __name__ == "__main__":
    # ⚠️ 专治 Windows 下的异步兼容性报错
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(setup_memory_db())
