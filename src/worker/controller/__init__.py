from pathlib import Path
from asyncio import sleep as async_sleep, subprocess, gather
from httpx import AsyncClient
from redis.asyncio import Redis
from taskiq import TaskiqScheduler, TaskiqState
from taskiq_redis import (
    ListRedisScheduleSource,
    RedisAsyncResultBackend,
    RedisStreamBroker,
)
from worker.core.lifespan import Lifespan
from worker.core.queue import Queue
from worker.core.router import Router
from shared.queue.client import Client
from shared.config.locker import Locker
from shared.log.helpers.core import build as core_log
from shared.models.worker import LifespanContext, WorkerInitContext
from shared.models.constants import Events, LogLevel, JobTypes
from shared.models.log import CoreError


locker = Locker()
router = Router()
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
        Queue=queue,
        AsyncSleep=async_sleep,
        SubProcess=subprocess,
        Gather=gather,
        EnqueueGate=gate_path.is_file(),
    )
)


async def enqueue_all(context: TaskiqState, job_type: JobTypes) -> list:
    configs = context.reader.startup_configs(job_type)
    client = Client(context)
    return await context.gather(*[client.enqueue(c, 0) for c in configs])


async def jobs(context: TaskiqState, job_type: JobTypes) -> None:
    config_log = context.config_log
    try:
        response = await enqueue_all(context, job_type)
        msg = f"{config_log.Service} startup. {job_type} Jobs Queued: {response}"
        core = core_log(config_log, LogLevel.INFO, Events.STARTUP, msg)
        context.log.write_core(core)
    except Exception as e:  # pylint: disable=broad-except
        msg = f"{config_log.Service} startup Failure for jobtype: {job_type}"
        core = core_log(config_log, LogLevel.ERROR, Events.STARTUP, msg)
        error = context.log_error_helper.trace_back_nfo(e)
        context.log.write_core_error(CoreError(Core=core, Error=error))


async def startup(context: TaskiqState) -> None:
    context.delay_dispatcher = delay_dispatcher
    context.delay_source = delay_source
    await delay_dispatcher.startup()
    await lifespan.startup(context)
    config_log = context.config_log
    try:
        context.http_client = AsyncClient(timeout=60)
        if context.config_worker.StartUp is True:
            for jt in JobTypes:
                await jobs(context, jt)
        core = core_log(
            config_log, LogLevel.INFO, Events.STARTUP, "http client startup"
        )
        context.log.write_core(core)
    except Exception as e:  # pylint: disable=broad-except
        msg = "http client startup Failure"
        core = core_log(config_log, LogLevel.ERROR, Events.STARTUP, msg)
        error = context.log_error_helper.trace_back_nfo(e)
        context.log.write_core_error(CoreError(Core=core, Error=error))


async def shutdown(context: TaskiqState) -> None:
    config_log = context.config_log
    if context.get("db"):
        await lifespan.shutdown(context)
        await delay_dispatcher.shutdown()
        await redis_client.aclose()
    if context.get("http_client"):
        await context.http_client.aclose()
    core = core_log(config_log, LogLevel.INFO, Events.SHUTDOWN, "Worker Shutdown")
    context.log.write_core(core)


queue.task(router.hello, task_name=JobTypes.HELLO)
queue.on_event("startup")(startup)
queue.on_event("shutdown")(shutdown)
