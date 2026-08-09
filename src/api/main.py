# pylint: disable=duplicate-code
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, Response
from redis.asyncio import Redis
from starlette.responses import PlainTextResponse
from taskiq import TaskiqState
from taskiq_redis import (
    ListRedisScheduleSource,
    RedisAsyncResultBackend,
    RedisStreamBroker,
)
from api.metadata import tags
from api.v1 import flush
from api.v1.info import info, ready, state
from shared.config.locker import Locker
from shared.db import Engine
from shared.log.helpers.api_log_serializer import LogSerializer
from shared.log.helpers.core import build as core_log
from shared.log.helpers.error import Error
from shared.log.writer import Writer
from shared.models.api import ASGIEvent, RootResponse
from shared.models.constants import Events, LogLevel, UserContext
from shared.models.db import DBStartUpContext
from shared.models.log import EventError
from shared.models.worker import WorkerInitContext
from shared.queue.client import Client
from shared.queue.queue import Queue
from worker.core.router import register

locker = Locker()
config_log = locker.log()
config_awork = locker.awork()
config_redis = locker.redis()
redis_url = f"redis://{config_redis.Host}:{config_redis.Port}"
redis_client = Redis.from_url(redis_url)
queue_context = WorkerInitContext(
    Broker=RedisStreamBroker,
    Backend=RedisAsyncResultBackend,
    RedisURL=redis_url,
    RedisClient=redis_client,
)
queue = Queue(queue_context, config_redis).build()
register(queue)
delay_source = ListRedisScheduleSource(redis_url)
gate_path = Path(config_awork.GatePath)


@asynccontextmanager
async def lifespan(app: FastAPI):
    s = app.state
    s.log = Writer(config_log)
    s.log_error_helper = Error()
    s.format_log = LogSerializer()
    s.user_context = UserContext.APP
    s.config_log = config_log
    s.app_version = config_awork.AppVersion
    s.enqueue_gate = gate_path.is_file()
    db_startup_ctx = DBStartUpContext(
        Log=s.log,
        UserContext=s.user_context,
        Config=config_log,
        LogErrorHelper=s.log_error_helper,
        DBMaxPool=config_awork.DBMaxPool,
    )
    s.db = Engine(db_startup_ctx)
    worker_context = TaskiqState()
    worker_context.queue = queue
    worker_context.delay_source = delay_source
    worker_context.redis_client = redis_client
    worker_context.config_log = config_log
    worker_context.log = s.log
    worker_context.enqueue_gate = s.enqueue_gate
    s.worker = Client(worker_context)
    await s.db.startup()
    await queue.startup()
    await delay_source.startup()
    msg = "API Service Startup complete"
    core = core_log(config_log, LogLevel.INFO, Events.STARTUP, msg)
    s.log.write_core(core)
    try:
        yield
    finally:
        await delay_source.shutdown()
        await queue.shutdown()
        await redis_client.aclose()
        await s.db.shutdown()
        msg = "API Service Shutdown complete"
        core = core_log(config_log, LogLevel.INFO, Events.SHUTDOWN, msg)
        s.log.write_core(core)


def create_api() -> FastAPI:
    _api = FastAPI(
        title="Async API Service",
        version=f"Version: {config_awork.AppVersion}",
        openapi_tags=tags(),
        lifespan=lifespan,
    )

    @_api.middleware("http")
    async def _access_mw(
        request: Request, call_next
    ):  # pylint: disable=too-many-locals
        start = config_log.TimeCounter()
        request.app.state.txid = request.app.state.format_log.transaction_id(request)
        try:
            response: Response = await call_next(request)
            error = None
            trace_back_nfo = None
        except Exception as e:  # pylint: disable=broad-except
            response = PlainTextResponse(
                "Unknown Internal Server Error",
                status_code=500,
            )
            error = e
            trace_back_nfo = request.app.state.log_error_helper.trace_back_nfo(e)
        finally:
            duration = int((config_log.TimeCounter() - start) * 1000)
            msg = request.app.state.format_log.message(response)
            core_event = core_log(config_log, LogLevel.INFO, Events.ACCESS, msg)
            event_input = ASGIEvent(
                Request=request, Response=response, DurationMS=duration
            )
            log_dto = request.app.state.format_log.build(core_event, event_input)
            if error is None:
                request.app.state.log.write_event(dto=log_dto)
            else:
                err_core = core_log(
                    config_log, LogLevel.ERROR, Events.HTTP_ERROR, str(error)
                )
                error_event_input = ASGIEvent(
                    Request=request, Response=response, DurationMS=duration
                )
                error_event_dto = request.app.state.format_log.build(
                    err_core, error_event_input
                )
                error_event_error_dto = EventError(
                    Core=error_event_dto.Core,
                    Event=error_event_dto.Event,
                    Error=trace_back_nfo,
                )
                request.app.state.log.write_event_error(dto=error_event_error_dto)
        return response

    @_api.get("/api/v1")
    async def root() -> RootResponse:
        """Application Root"""
        return RootResponse(Message="Async API Service is up!")

    _api.include_router(info.router, prefix="/api/v1", tags=["info"])
    _api.include_router(state.router, prefix="/api/v1", tags=["info"])
    _api.include_router(ready.router, prefix="/api/v1", tags=["info"])
    _api.include_router(flush.router, prefix="/api/v1", tags=["flush"])

    return _api


api = create_api()
