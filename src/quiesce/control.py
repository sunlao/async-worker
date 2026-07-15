from time import monotonic
from uuid import uuid4
from asyncio import sleep as async_sleep, run
from arq import create_pool
from quiesce.gate import Gate
from quiesce.docker import sigterm, restart
from quiesce.queue import Queue
from shared.config.locker import Locker
from shared.db import Engine
from shared.helper.ops_ledger import OpsLedger
from shared.log.helpers.core import build as core_log
from shared.log.writer import Writer
from shared.log.helpers.error import Error
from shared.models.api import AdminExecutionResults, QuiesceQueue
from shared.models.constants import Events, LogLevel, UserContext
from shared.models.db import DBStartUpContext
from shared.models.log import Event, CoreError
from shared.queue.arq_client import ARQClient

locker = Locker()
config_log = locker.log()
log = Writer(config_log)


class Control:

    def __init__(self):
        self.config_quiesce = locker.quiesce()
        self.gate = Gate(self.config_quiesce, uuid4)
        self.arq = ARQClient(locker.redis(), async_sleep, create_pool)
        db_startup_ctx = DBStartUpContext(
            Log=log,
            UserContext=UserContext.DATA,
            Config=config_log,
            LogErrorHelper=Error(),
            DBMaxPool=self.config_quiesce.DBMaxPool,
        )
        self.db = Engine(db_startup_ctx)
        self.quiesce_queue = QuiesceQueue(
            Arq=self.arq,
            Config=self.config_quiesce,
            Sleep=async_sleep,
            Monotonic=monotonic,
            UUID=uuid4,
        )

    def _event_log(self, event_results):
        msg = "Quiesce: Execution Events"
        core = core_log(config_log, LogLevel.INFO, Events.QUIESCE, msg)
        log_dto: Event[AdminExecutionResults] = Event(Core=core, Event=event_results)
        log.write_event(log_dto)

    async def startup(self):
        await self.arq.startup()
        await self.db.startup()
        msg = "Quiesce: Startup Complete"
        core = core_log(config_log, LogLevel.INFO, Events.STARTUP, msg)
        log.write_core(core)

    async def shutdown(self):
        await self.arq.shutdown()
        await self.db.shutdown()
        msg = "Quiesce: Shutdown Complete"
        core = core_log(config_log, LogLevel.INFO, Events.SHUTDOWN, msg)
        log.write_core(core)

    async def execute(self):
        await self.startup()
        ops_ledger = OpsLedger(self.arq, self.db, uuid4)
        queue = Queue(self.quiesce_queue)

        self._event_log(self.gate.close())

        await async_sleep(3)

        self._event_log(await sigterm())
        self._event_log(await queue.drain())
        self._event_log(await ops_ledger.load())
        self._event_log(await queue.delete())
        self._event_log(await restart())
        self._event_log(self.gate.open())

        await self.shutdown()


async def _main():
    try:
        await Control().execute()
    except Exception as e:  # pylint: disable=broad-except
        e_msg = "Quiesce Failure"
        e_core = core_log(config_log, LogLevel.INFO, Events.QUIESCE, e_msg)
        e_error = Error().trace_back_nfo(e)
        log.write_core_error(CoreError(Core=e_core, Error=e_error))


if __name__ == "__main__":
    run(_main())
