import os
import asyncio
from redis.asyncio import Redis
from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker
from sw.middleware import ActiveJobMiddleware

redis_url = f"redis://{os.environ['REDIS_HOST']}:{os.environ['REDIS_PORT']}"
redis = Redis.from_url(redis_url)
result_backend = RedisAsyncResultBackend(redis_url=redis_url)
broker = RedisStreamBroker(url=redis_url)
middleware = ActiveJobMiddleware(redis)
broker = broker.with_result_backend(result_backend)
broker = broker.with_middlewares(middleware)


@broker.task
async def example(job_id: int) -> str:
    await asyncio.sleep(10)
    print(f"job_id: {job_id}")
    return f"completed {job_id}"
