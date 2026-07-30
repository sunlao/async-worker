from pathlib import Path
from asyncio import sleep as async_sleep, subprocess
from redis.asyncio import Redis
from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker
from shared.config.locker import Locker
from shared.models.worker import LifespanContext, WorkerInit
from cp.lifespan import Lifespan
from cp.queue import Queue


locker = Locker()
config_redis = locker.redis()
config_worker = locker.worker()
worker_init = WorkerInit(
    Broker=RedisStreamBroker, Backend=RedisAsyncResultBackend, RedisClient=Redis
)
queue = Queue(worker_init, config_redis).build()
gate_path = Path(config_worker.GatePath)
lifespan = Lifespan(
    LifespanContext(
        Locker=locker,
        AsyncSleep=async_sleep,
        SubProcess=subprocess,

        EnqueueGate=gate_path.is_file(),
    )
)

queue.on_event("startup")(lifespan.startup)
queue.on_event("shutdown")(lifespan.shutdown)
