from pathlib import Path
from asyncio import sleep as async_sleep, subprocess
from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker
from taskiq import TaskiqEvents, TaskiqState, TaskiqDepends
from taskiq.middlewares import SmartRetryMiddleware
from httpx import AsyncClient
from worker.helpers.lifecycle import LifeCycle
from worker.handler.movement import Movement as MHandler
from worker.handler.admin import Admin as AHandler
from worker.helpers.startup import Startup
from worker.helpers.flush import save
from shared.config.locker import Locker
from shared.log.helpers.core import build as core_log
from shared.models.constants import Events, LogLevel, JobTypes
from shared.models.worker import JobConfig, LifeCycleContext
from shared.models.log import CoreError

locker = Locker()
config_worker = locker.worker()
gate_path = Path(config_worker.GatePath)
life_cycle_init = LifeCycleContext(
    Locker=locker,
    AsyncSleep=async_sleep,
    SubProcess=subprocess,
    Broker=RedisStreamBroker,
    Backend=RedisAsyncResultBackend,
    EnqueueGate=gate_path.is_file(),
)
lifecycle = LifeCycle(life_cycle_init)
broker = lifecycle.broker

async def admin(config: JobConfig, state: TaskiqState = TaskiqDepends()):
    result = await AHandler(state).handle(config.Config, **config.KWARGS)
    if result.Event.Status is False:
        raise RuntimeError("Admin job failed")
    return result

async def movement(config: JobConfig, state: TaskiqState = TaskiqDepends()):
    result = await MHandler(state).handle(config.Config, **config.KWARGS)
    if result.Event.Status is False:
        raise RuntimeError("Movement job failed")
    return result

async def flush(
    state: TaskiqState = TaskiqDepends(),
):
    save(state)


async def jobs(state: TaskiqState, job_type: JobTypes) -> None:
    config_log = state.config_log
    try:
        response = await Startup(state).enqueue(job_type)
        msg = f"{config_log.Service} startup. {job_type} Jobs Queued: {response}"
        core = core_log(config_log, LogLevel.INFO, Events.STARTUP, msg)
        state.log.write_core(core)
    except Exception as e:  # pylint: disable=broad-except
        msg = f"{config_log.Service} startup Failure for jobtype: {job_type}"
        core = core_log(config_log, LogLevel.ERROR, Events.STARTUP, msg)
        error = state.log_error_helper.trace_back_nfo(e)
        state.log.write_core_error(CoreError(Core=core, Error=error))


async def worker_shutdown(state: TaskiqState) -> None:
    config_log = state.config_log
    if state.get("db"):
        await lifecycle.db_shutdown(state)
    if state.get("http_client"):
        await state.http_client.aclose()
    core = core_log(config_log, LogLevel.INFO, Events.SHUTDOWN, "Worker Shutdown")
    state.log.write_core(core)
    save(state)


async def worker_startup(state: TaskiqState) -> None:
    await lifecycle.start_all(state)
    config_log = state.config_log
    if config_worker.StartUp is True:
        for jt in JobTypes:
            await jobs(state, jt)
    try:
        state.http_client = AsyncClient(timeout=60)
        core = core_log(
            config_log, LogLevel.INFO, Events.STARTUP, "http client startup"
        )
        state.log.write_core(core)
    except Exception as e:  # pylint: disable=broad-except
        msg = "http client startup Failure"
        core = core_log(config_log, LogLevel.ERROR, Events.STARTUP, msg)
        error = state.log_error_helper.trace_back_nfo(e)
        state.log.write_core_error(CoreError(Core=core, Error=error))


broker.add_event_handler(
    TaskiqEvents.WORKER_STARTUP,
    worker_startup,
)

broker.add_event_handler(
    TaskiqEvents.WORKER_SHUTDOWN,
    worker_shutdown,
)

broker.with_middlewares(
    SmartRetryMiddleware(
        default_retry_label=False,
        default_delay=60,
    )
)

broker.task(admin,retry_on_error=True,max_retries=3,delay=60)
broker.task(movement,retry_on_error=True,max_retries=3,delay=60)
broker.task(flush)
