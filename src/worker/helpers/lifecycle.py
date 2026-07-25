from taskiq import TaskiqState
from shared.config.reader import Reader
from shared.db import Engine
from shared.log.writer import Writer
from shared.log.helpers.error import Error
from shared.models.config import ReaderConfig, Redis
from shared.models.constants import UserContext
from shared.models.db import DBStartUpContext
from shared.models.worker import LifeCycleContext


# pylint: disable=too-many-instance-attributes
class LifeCycle:
    """Worker lifecyle utility Class"""

    def __init__(self, context: LifeCycleContext):
        self.life_cycle = context
        self.locker = context.Locker
        config_redis = self.locker.redis()
        self.config_log = self.locker.log()
        self.config_worker = self.locker.worker()
        self.reader = Reader(
            ReaderConfig(
                JobPath=self.config_worker.JobPath,
                JobVersion=self.config_worker.JobVersion,
            )
        )
        self.enqueue_gate = context.EnqueueGate
        self._broker(config_redis, context)

    def _broker(self, config_redis: Redis, context: LifeCycleContext) -> None:
        redis_url = f"redis://{config_redis.Host}:{config_redis.Port}"
        backend = context.Backend(redis_url=redis_url, result_ex_time=14400)
        context.Broker(url=redis_url).with_result_backend(backend)

    async def _db_startup(self, state: TaskiqState, context: DBStartUpContext) -> None:
        db = Engine(context)
        await db.startup()
        async with db.client() as conn:
            row = await conn.fetchrow("select true as check")
        if row["check"] is not True:
            raise RuntimeError("DB probe failed (unexpected result)")
        state.db = db

    async def db_shutdown(self, state: TaskiqState) -> None:
        """Shutdown the db before worker shutdown"""
        await state.db.shutdown()

    async def start_all(self, state: TaskiqState) -> None:
        """Start up and create global context for the worker"""
        state.log = Writer(self.config_log)
        state.config_log = self.config_log
        state.log_error_helper = Error()
        state.asubprocess = self.life_cycle.SubProcess
        state.data_dir = self.config_worker.DataDir
        state.asleep = self.life_cycle.AsyncSleep
        state.config_worker = self.config_worker
        state.reader = self.reader
        state.enqueue_gate = self.enqueue_gate
        db_startup_ctx = DBStartUpContext(
            Log=state.log,
            UserContext=UserContext.DATA,
            Config=state.config_log,
            LogErrorHelper=state.log_error_helper,
            DBMaxPool=self.config_worker.DBMaxPool,
        )
        await self._db_startup(state, db_startup_ctx)
