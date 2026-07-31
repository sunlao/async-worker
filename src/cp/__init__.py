from pathlib import Path
from asyncio import sleep as async_sleep, subprocess
from redis.asyncio import Redis
from taskiq import TaskiqScheduler, TaskiqState
from taskiq_redis import (
    ListRedisScheduleSource,
    RedisAsyncResultBackend,
    RedisStreamBroker,
)
from cp.lifespan import Lifespan
from cp.queue import Queue
from shared.config.locker import Locker
from shared.models.worker import LifespanContext, WorkerInitContext


locker = Locker()
config_redis = locker.redis()
config_worker = locker.worker()
redis_url = f"redis://{config_redis.Host}:{config_redis.Port}"
redis_client = Redis.from_url(redis_url)
worker_init = WorkerInitContext(
    Broker=RedisStreamBroker,
    Backend=RedisAsyncResultBackend,
    RedisURL=redis_url,
    RedisClient=redis_client,
)
queue = Queue(worker=worker_init, config=config_redis).build()
delay_source = ListRedisScheduleSource(redis_url)
delay_dispatcher = TaskiqScheduler(broker=queue, sources=[delay_source])
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
    state.redis_client = worker_init.RedisClient
    state.delay_dispatcher = delay_dispatcher
    await delay_dispatcher.startup()
    await lifespan.startup(state)


async def shutdown(state: TaskiqState) -> None:
    await lifespan.shutdown(state)
    await delay_dispatcher.shutdown()
    await redis_client.aclose()


queue.on_event("startup")(startup)
queue.on_event("shutdown")(shutdown)
