from asyncio import sleep as async_sleep, subprocess
from pathlib import Path

from redis.asyncio import Redis
from taskiq import TaskiqState
from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker

from cp.lifespan import Lifespan
from cp.queue import Queue
from shared.config.locker import Locker
from shared.models.worker import LifespanContext, WorkerInit


locker = Locker()
config_redis = locker.redis()
config_worker = locker.worker()

worker_init = WorkerInit(
    Broker=RedisStreamBroker,
    Backend=RedisAsyncResultBackend,
    RedisClient=Redis,
)

redis_url = (
    f"redis://{config_redis.redis.Host}:"
    f"{config_redis.redis.Port}"
)
redis_client = worker_init.RedisClient.from_url(redis_url)

queue = Queue(
    worker=worker_init,
    config=config_redis,
    redis_client=redis_client,
).build()

gate_path = Path(config_worker.GatePath)

lifespan = Lifespan(
    LifespanContext(
        Locker=locker,
        AsyncSleep=async_sleep,
        SubProcess=subprocess,
        EnqueueGate=gate_path.is_file(),
    )
)


async def startup(state: TaskiqState) -> None:
    state.redis = redis_client
    await lifespan.startup(state)


async def shutdown(state: TaskiqState) -> None:
    await lifespan.shutdown(state)
    await redis_client.aclose()


queue.on_event("startup")(startup)
queue.on_event("shutdown")(shutdown)