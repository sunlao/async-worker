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
from cp.router import Router
from shared.config.locker import Locker
from shared.models.worker import LifespanContext, WorkerInitContext
from shared.models.constants import JobTypes


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


async def startup(context: TaskiqState) -> None:
    context.redis_client = worker_init.RedisClient
    context.delay_dispatcher = delay_dispatcher
    context.delay_source = delay_source
    await delay_dispatcher.startup()
    await lifespan.startup(context)
    router = Router(context)
    queue.task(router.hello, task_name=JobTypes.HELLO)


async def shutdown(context: TaskiqState) -> None:
    await lifespan.shutdown(context)
    await delay_dispatcher.shutdown()
    await redis_client.aclose()


queue.on_event("startup")(startup)
queue.on_event("shutdown")(shutdown)
