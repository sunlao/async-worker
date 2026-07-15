from asyncio import Lock
from collections import deque
from asyncpg import Connection
from shared.models.db import (
    DBStartUpContext,
    DBConnectEvent,
    DBConnInput,
    DBPoolOutcome,
)
from shared.db.helpers.utility import connection
from shared.log.helpers.core import build as core_log
from shared.models.constants import LogLevel, Events
from shared.models.log import Event


# pylint: disable=too-many-instance-attributes
class Pool:
    """Create a collection of reusable connections"""

    def __init__(self, startup_ctx: DBStartUpContext):
        self.log_config = startup_ctx.Config
        self.log = startup_ctx.Log
        self.user_ctx = startup_ctx.UserContext
        self.max_pool = startup_ctx.DBMaxPool
        self.conns: deque[Connection] = deque()
        self.lock = Lock()  # only lock when pop & append from self.conns
        self.is_closing = False

    async def _new_conn(
        self, elapsed: float, outcome: DBPoolOutcome, msg: str
    ) -> Connection:
        input_dto = DBConnInput(
            UserContext=self.user_ctx, Config=self.log_config, StartElapsed=elapsed
        )
        new_conn_dto = await connection(input_dto)
        event = DBConnectEvent(
            ConnectElapsed_ms=new_conn_dto.Elapsed_ms, DBOpenOutcome=outcome
        )
        core = core_log(self.log_config, LogLevel.INFO, Events.DBOPEN, msg)
        self.log.write_event(dto=Event(Core=core, Event=event))
        return new_conn_dto.Connection

    async def _is_active(self, conn) -> bool:
        try:
            row = await conn.fetchrow("SELECT true as check")
            if row["check"] is True:
                return True
        except Exception:  # pylint: disable=broad-exception-caught
            return False
        return False

    async def acquire(self) -> Connection:
        """Aquire an active connection from collection
        Reuse if available or make connection
         - Invactive
         - New
        """
        start_elapsed = self.log_config.TimeCounter()
        if self.is_closing:
            raise RuntimeError("DB Closing: Can't acquire new connection")
        async with self.lock:
            conn = self.conns.pop() if self.conns else None
        if await self._is_active(conn):
            msg = "DB Open Connection"
            core = core_log(self.log_config, LogLevel.INFO, Events.DBOPEN, msg)
            elapsed = int((self.log_config.TimeCounter() - start_elapsed) * 1000)
            event = DBConnectEvent(
                ConnectElapsed_ms=elapsed, DBOpenOutcome=DBPoolOutcome.REUSE
            )
            self.log.write_event(dto=Event(Core=core, Event=event))
            return conn
        if conn is not None:
            msg = "Inactive Connection"
            await self._new_conn(start_elapsed, DBPoolOutcome.RETRY, msg)
        return await self._new_conn(start_elapsed, DBPoolOutcome.NEW, "New Connection")

    async def recycle(self, conn: Connection) -> None:
        """Append active connection back to collection for reuse"""
        async with self.lock:
            if (
                conn is not None
                and not conn.is_closed()
                and len(self.conns) < self.max_pool
            ):
                self.conns.append(conn)

    async def empty(self) -> None:
        """Empty connection collection and close all connections"""
        self.is_closing = True
        while True:
            async with self.lock:
                if not self.conns:
                    break
                c = self.conns.pop()
            if not c.is_closed():
                await c.close()
        self.is_closing = False
