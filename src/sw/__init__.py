import asyncio
from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker

redis_url = "redis://localhost:6379"

result_backend = RedisAsyncResultBackend(
    redis_url=redis_url,
)

broker = RedisStreamBroker(
    url=redis_url,
).with_result_backend(result_backend)


@broker.task
async def example(job_id: int) -> str:
    await asyncio.sleep(30)
    return f"completed {job_id}"