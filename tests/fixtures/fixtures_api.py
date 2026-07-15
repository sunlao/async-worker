# pylint: disable=duplicate-code
from contextlib import asynccontextmanager
from pytest import fixture
from fastapi import FastAPI, Request
from shared.log.helpers.api_log_serializer import LogSerializer
from shared.log.writer import Writer
from shared.log.helpers.error import Error
from shared.log.helpers.core import build as core_log
from shared.models.constants import UserContext, Events, LogLevel


@asynccontextmanager
async def _app_state(engine, arq_client, config_log, config_awork):
    app = FastAPI()
    s = app.state
    s.log = Writer(config_log)
    s.log_error_helper = Error()
    s.format_log = LogSerializer()
    s.user_context = UserContext.APP
    s.config_log = config_log
    s.app_version = config_awork.AppVersion
    s.enqueue_gate = False
    s.db = engine
    s.arq_client = arq_client
    await s.arq_client.startup()
    await s.db.startup()
    if not await s.arq_client.redis_ping():
        await s.db.shutdown()
        await s.arq_client.shutdown()
        msg = "Failed Redis Ping on startup"
        s.log.write_core(core_log(config_log, LogLevel.ERROR, Events.STARTUP, msg))
        raise RuntimeError("Redis ping failed during startup")
    s.log.write_core(
        core_log(config_log, LogLevel.INFO, Events.STARTUP, "Startup complete")
    )
    try:
        yield app
    finally:
        await s.db.shutdown()
        s.log.write_core(
            core_log(config_log, LogLevel.INFO, Events.SHUTDOWN, "Shutdown complete")
        )


@fixture(name="api_with_state")
async def f_api_with_state(engine, arq_client, config_log, config_awork):
    async with _app_state(engine, arq_client, config_log, config_awork) as app:
        yield app


@fixture
async def api_request(api_with_state: FastAPI) -> Request:
    scope = {
        "type": "http",
        "app": api_with_state,
        "headers": [],
        "method": "GET",
        "path": "/_test",
        "query_string": b"",
    }
    return Request(scope)
