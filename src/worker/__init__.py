from pathlib import Path
from asyncio import sleep as asleep, subprocess, gather, create_task, CancelledError
from httpx import AsyncClient
from redis.asyncio import Redis
from taskiq import TaskiqEvents, TaskiqScheduler, TaskiqState
from taskiq.api import run_scheduler_task
from taskiq_redis import (
    ListRedisScheduleSource,
    RedisAsyncResultBackend,
    RedisStreamBroker,
)
from shared.config.locker import Locker
from shared.log.helpers.core import build as core_log
from shared.models.constants import Events, LogLevel, JobTypes, EnqueueTypes
from shared.models.log import CoreError
from shared.models.worker import LifespanContext, WorkerInitContext
from shared.queue.client import Client
from worker.core.lifespan import Lifespan
from worker.core.queue import Queue
from worker.core.router import register

locker = Locker()
config_redis = locker.redis()
config_worker = locker.worker()
redis_url = f"redis://{config_redis.Host}:{config_redis.Port}"
redis_client = Redis.from_url(redis_url)
worker_context = WorkerInitContext(
    Broker=RedisStreamBroker,
    Backend=RedisAsyncResultBackend,
    RedisURL=redis_url,
    RedisClient=redis_client,
)

queue = Queue(worker_context, config_redis).build()
register(queue)
delay_source = ListRedisScheduleSource(redis_url)
delay_dispatcher = TaskiqScheduler(broker=queue, sources=[delay_source])
gate_path = Path(config_worker.GatePath)
lifespan_context = LifespanContext(
    Locker=locker,
    Queue=queue,
    AsyncSleep=asleep,
    SubProcess=subprocess,
    Gather=gather,
    EnqueueGate=gate_path.is_file(),
)
lifespan = Lifespan(lifespan_context)


async def enqueue_all(context: TaskiqState, job_type: JobTypes) -> list:
    """Async enqueue startup elgible jobs with overide delay of 1 second by type"""
    configs = context.job.startup_configs(job_type)
    client = Client(context)
    return await context.gather(
        *[client.enqueue(c, EnqueueTypes.START_UP, 1) for c in configs]
    )


async def jobs(context: TaskiqState, job_type: JobTypes) -> None:
    """Send All startup eligble jobs type shared enqueue client"""
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
    """Framework startup
    - create and start resources
    - edge injectiion of all side effects
    - intit elible jobs for startup
    """
    context.redis_client = worker_context.RedisClient
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
        await redis_client.aclose()
    if context.get("http_client"):
        await context.http_client.aclose()
    core = core_log(config_log, LogLevel.INFO, Events.SHUTDOWN, "Worker Shutdown")
    context.log.write_core(core)


async def delay_startup(context: TaskiqState) -> None:
    context.delay_source = delay_source
    context.delay_dispatcher = create_task(run_scheduler_task(delay_dispatcher))


async def delay_shutdown(context: TaskiqState) -> None:
    context.delay_dispatcher.cancel()
    try:
        await context.delay_dispatcher
    except CancelledError:
        pass


queue.on_event(TaskiqEvents.WORKER_STARTUP)(delay_startup)
queue.on_event(TaskiqEvents.WORKER_STARTUP)(startup)
queue.on_event(TaskiqEvents.WORKER_SHUTDOWN)(delay_shutdown)
queue.on_event(TaskiqEvents.WORKER_SHUTDOWN)(shutdown)
