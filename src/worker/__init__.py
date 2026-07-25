from pathlib import Path
from datetime import timedelta
from asyncio import sleep as async_sleep, subprocess
from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker
from taskiq import TaskiqEvents, TaskiqState
from httpx import AsyncClient
from worker.helpers.lifecycle import LifeCycle
from worker.handler.movement import Movement as MHandler
from worker.handler.admin import Admin as AHandler
from worker.helpers.startup import Startup
from worker.helpers.flush import save
from shared.config.locker import Locker
from shared.log.helpers.core import build as core_log
from shared.models.constants import Events, LogLevel, JobTypes
from shared.models.worker import JobConfig, Lifecycle
from shared.models.log import CoreError

locker = Locker()
config_worker = locker.worker()
gate_path = Path(config_worker.GatePath)
life_cycle = Lifecycle(
    Locker=locker,
    AsyncSleep=async_sleep,
    SubProcess=subprocess,
    Broker=RedisStreamBroker,
    Backend=RedisAsyncResultBackend,
    EnqueueGate=gate_path.is_file(),
)

utility = LifeCycle(life_cycle)

async def admin(ctx, config: JobConfig):
    """Routes all admin jobs to it's Handler"""

    result = await AHandler(ctx).handle(config.Config, **config.KWARGS)
    if result.Event.Status is False and ctx["job_try"] < config.Config.Retry:
        raise Retry(defer=timedelta(minutes=1))
    return result


async def movement(ctx, config: JobConfig):
    """Routes all movement jobs to it's Handler"""

    result = await MHandler(ctx).handle(config.Config, **config.KWARGS)
    if result.Event.Status is False and ctx["job_try"] < config.Config.Retry:
        raise Retry(defer=timedelta(minutes=1))
    return result

async def flush(ctx):
    """Support CI Code Coverage
    - Only used in ENV: ci
    - Disabled in all other environments"""
    save(ctx)

async def worker_shutdown(ctx) -> None:
    config_log = ctx["config_log"]
    if ctx.get("db"):
        await utility.db_shutdown(ctx)
    if ctx.get("arq_client"):
        await ctx["arq_client"].shutdown()
    await ctx["http_client"].aclose()
    core = core_log(config_log, LogLevel.INFO, Events.SHUTDOWN, "Worker Shutdown")
    ctx["log"].write_core(core)
    save(ctx)

async def jobs(ctx, job_type: JobTypes) -> None:
    config_log = ctx["config_log"]
    try:
        response = await Startup(ctx).enqueue(job_type)
        msg = f"{config_log.Service} startup. {job_type} Jobs Queued: {response}"
        core = core_log(config_log, LogLevel.INFO, Events.STARTUP, msg)
        ctx["log"].write_core(core)
    except Exception as e:  # pylint: disable=broad-except
        msg = f"{config_log.Service} startup Failure for jobtype: {job_type}"
        core = core_log(config_log, LogLevel.ERROR, Events.STARTUP, msg)
        error = ctx["log_error_helper"].trace_back_nfo(e)
        ctx["log"].write_core_error(CoreError(Core=core, Error=error))

async def worker_startup(state: TaskiqState) -> None:
    ctx = {}
    await utility.start_all(ctx)
    config_log = ctx["config_log"]
    if config_worker.StartUp is True:
        for jt in JobTypes:
            await jobs(ctx, jt)
    try:
        ctx["http_client"] = AsyncClient(timeout=60)
        core = core_log(
            config_log, LogLevel.INFO, Events.STARTUP, "http client startup"
        )
        ctx["log"].write_core(core)
    except Exception as e:  # pylint: disable=broad-except
        msg = "http client startup Failure"
        core = core_log(config_log, LogLevel.ERROR, Events.STARTUP, msg)
        error = ctx["log_error_helper"].trace_back_nfo(e)
        ctx["log"].write_core_error(CoreError(Core=core, Error=error))
    state.ctx = ctx

utility.broker.add_event_handler(
    TaskiqEvents.WORKER_STARTUP,
    worker_startup,
)

utility.broker.add_event_handler(
    TaskiqEvents.WORKER_SHUTDOWN,
    worker_shutdown,
)

utility.broker.task(admin)
utility.broker.task(movement)
utility.broker.task(flush)