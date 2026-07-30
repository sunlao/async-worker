from taskiq import TaskiqState
from shared.config.reader import Reader
from shared.db import Engine
from shared.log.helpers.error import Error
from shared.log.writer import Writer
from shared.models.config import ReaderConfig
from shared.models.constants import UserContext
from shared.models.db import DBStartUpContext
from shared.models.worker import LifespanContext


class Lifespan:
    def __init__(self, context: LifespanContext):
        self.context = context
        locker = context.Locker
        self.config_log = locker.log()
        self.config_worker = locker.worker()
        self.reader = Reader(
            ReaderConfig(
                JobPath=self.config_worker.JobPath,
                JobVersion=self.config_worker.JobVersion,
            )
        )

    async def _db_startup(
        self,
        state: TaskiqState,
        context: DBStartUpContext,
    ) -> None:
        db = Engine(context)
        await db.startup()
        async with db.client() as conn:
            row = await conn.fetchrow("select true as check")
        if row["check"] is not True:
            raise RuntimeError("DB probe failed")

        state.db = db

    async def startup(self, state: TaskiqState) -> None:
        state.log = Writer(self.config_log)
        state.config_log = self.config_log
        state.log_error_helper = Error()
        state.asubprocess = self.context.SubProcess
        state.asleep = self.context.AsyncSleep
        state.data_dir = self.config_worker.DataDir
        state.config_worker = self.config_worker
        state.reader = self.reader
        state.enqueue_gate = self.context.EnqueueGate
        await self._db_startup(
            state,
            DBStartUpContext(
                Log=state.log,
                UserContext=UserContext.DATA,
                Config=state.config_log,
                LogErrorHelper=state.log_error_helper,
                DBMaxPool=self.config_worker.DBMaxPool,
            ),
        )

    async def shutdown(self, state: TaskiqState) -> None:
        await state.db.shutdown()