import os
import logging
import asyncio
from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker

logger = logging.getLogger(__name__)
redis_url = f"redis://{os.environ['REDIS_HOST']}:{os.environ['REDIS_PORT']}"

result_backend = RedisAsyncResultBackend(
    redis_url=redis_url,
)

broker = RedisStreamBroker(
    url=redis_url,
).with_result_backend(result_backend)


@broker.task
async def example(job_id: int) -> str:
    await asyncio.sleep(10)
    logger.info("job_id: %s", job_id)
    return f"completed {job_id}"
