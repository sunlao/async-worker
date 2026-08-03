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
    """Worker helper to facilitate starup
     - configure context 
        - resources 
        - side effect injection
     - db startup / shutdown
     """

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
        self, worker_context: TaskiqState, db_context: DBStartUpContext
    ) -> None:
        db = Engine(db_context)
        await db.startup()
        async with db.client() as conn:
            row = await conn.fetchrow("select true as check")
        if row["check"] is not True:
            raise RuntimeError("DB probe failed")

        worker_context.db = db

    async def startup(self, context: TaskiqState) -> None:
        context.log = Writer(self.config_log)
        context.config_log = self.config_log
        context.log_error_helper = Error()
        context.asubprocess = self.context.SubProcess
        context.gather = self.context.Gather
        context.asleep = self.context.AsyncSleep
        context.data_dir = self.config_worker.DataDir
        context.config_worker = self.config_worker
        context.reader = self.reader
        context.enqueue_gate = self.context.EnqueueGate
        context.queue = self.context.Queue
        await self._db_startup(
            context,
            DBStartUpContext(
                Log=context.log,
                UserContext=UserContext.DATA,
                Config=context.config_log,
                LogErrorHelper=context.log_error_helper,
                DBMaxPool=self.config_worker.DBMaxPool,
            ),
        )

    async def shutdown(self, context: TaskiqState) -> None:
        await context.db.shutdown()
