# pylint: disable=duplicate-code
from pathlib import Path
from contextlib import asynccontextmanager
from asyncio import sleep as async_sleep
from starlette.responses import PlainTextResponse
from fastapi import FastAPI, Request, Response
from api.v1 import flush

# from arq import create_pool
from api.metadata import tags

# from api.v1 import enqueue
from api.v1.info import ready, info

# from shared.queue.client import ARQClient
from shared.log.helpers.api_log_serializer import LogSerializer
from shared.db import Engine
from shared.config.locker import Locker
from shared.log.writer import Writer
from shared.log.helpers.error import Error
from shared.log.helpers.core import build as core_log
from shared.models.constants import UserContext
from shared.models.constants import Events, LogLevel
from shared.models.api import ASGIEvent, RootResponse
from shared.models.db import DBStartUpContext
from shared.models.log import EventError

locker = Locker()
config_log = locker.log()
config_awork = locker.awork()
# redid_log = locker.redis()
# reader = Reader(
#     ReaderConfig(
#         JobPath=config_awork.JobPath,
#         JobVersion=config_awork.JobVersion,
#     )
# )
# arq = ARQClient(locker.redis(), async_sleep, create_pool)
gate_path = Path(config_awork.GatePath)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.log = Writer(config_log)
    app.state.log_error_helper = Error()
    app.state.format_log = LogSerializer()
    app.state.user_context = UserContext.APP
    # app.state.reader = reader
    app.state.config_log = config_log
    app.state.app_version = config_awork.AppVersion
    app.state.enqueue_gate = gate_path.is_file()
    db_startup_ctx = DBStartUpContext(
        Log=app.state.log,
        UserContext=app.state.user_context,
        Config=config_log,
        LogErrorHelper=app.state.log_error_helper,
        DBMaxPool=config_awork.DBMaxPool,
    )
    app.state.db = Engine(db_startup_ctx)
    # app.state.client = arq
    # await app.state.client.startup()
    await app.state.db.startup()
    # if not await app.state.client.redis_ping():
    #     await app.state.db.shutdown()
    #     # await app.state.client.shutdown()
    #     msg = "Failed Redis Ping on startup"
    #     core = core_log(config_log, LogLevel.ERROR, Events.STARTUP, msg)
    #     app.state.log.write_core(core)
    #     raise RuntimeError("Redis ping failed during startup")
    msg = "API Service Startup complete"
    core = core_log(config_log, LogLevel.INFO, Events.STARTUP, msg)
    app.state.log.write_core(core)
    try:
        yield
    finally:
        await app.state.db.shutdown()
        # await app.state.client.shutdown()
        msg = "API Service Shutdown complete"
        core = core_log(config_log, LogLevel.INFO, Events.SHUTDOWN, msg)
        app.state.log.write_core(core)


def create_api() -> FastAPI:
    _api = FastAPI(
        title="Async API Service",
        version=f"Version: {config_awork.AppVersion}",
        openapi_tags=tags(),
        lifespan=lifespan,
    )

    # used for central api logging events
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
                "Unknown Internal Server Error", status_code=500
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

    # routing
    _api.include_router(info.router, prefix="/api/v1", tags=["info"])
    _api.include_router(ready.router, prefix="/api/v1", tags=["info"])
    _api.include_router(flush.router, prefix="/api/v1", tags=["flush"])
    return _api


api = create_api()
