from contextlib import asynccontextmanager
from typing import Optional, AsyncIterator
from asyncpg import Connection
from shared.log.helpers.core import build as core_log
from shared.models.constants import LogLevel, Events
from shared.models.db import DBStartUpContext
from shared.db.pool import Pool


class Engine:
    """
    Single-role DB Engine: one role per process (e.g., API=APP, worker=DATA).
    Owns a single pool, a single lock, and lifecycle (open/close).
    """

    def __init__(self, startup_ctx: DBStartUpContext):
        self.log_config = startup_ctx.Config
        self.log = startup_ctx.Log
        self.user_ctx = startup_ctx.UserContext
        self.conn: Optional[Connection] = None
        self.pool = Pool(startup_ctx)

    async def startup(self) -> None:
        core = core_log(self.log_config, LogLevel.INFO, Events.DBOPEN, "DB Startup")
        self.log.write_core(core)
        self.conn = await self.pool.acquire()

    async def shutdown(self) -> None:
        await self.pool.empty()
        self.conn = None
        core = core_log(self.log_config, LogLevel.INFO, Events.DBOPEN, "DB Shutdown")
        self.log.write_core(core)

    @asynccontextmanager
    async def client(self) -> AsyncIterator[Connection]:
        conn = await self.pool.acquire()
        try:
            yield conn
        finally:
            await self.pool.recycle(conn)
