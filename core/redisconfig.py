import redis.asyncio as redis
from typing import AsyncGenerator

url = "redis://127.0.0.1:6379/0"
#decode_responses=True 会自动将拿到的 bytes 解码为 str
redis_client = redis.from_url(url,encoding="utf-8",decode_responses=True)

async def get_redis_client() -> AsyncGenerator[redis.Redis,None]:
    yield redis_client