from arq.connections import RedisSettings
from shared.config.reader import Reader
from shared.db import Engine
from shared.log.writer import Writer
from shared.log.helpers.error import Error
from shared.models.config import ReaderConfig
from shared.models.constants import UserContext
from shared.models.db import DBStartUpContext
from shared.models.worker import Lifecycle


# pylint: disable=too-many-instance-attributes
class LifeCycle:
    """Utility to set queue lifecyle"""

    def __init__(self, life_cycle: Lifecycle):
        self.life_cycle = life_cycle
        self.locker = life_cycle.Locker
        self.config_redis = self.locker.redis()
        self.config_log = self.locker.log()
        self.config_worker = self.locker.worker()
        self.reader = Reader(
            ReaderConfig(
                JobPath=self.config_worker.JobPath,
                JobVersion=self.config_worker.JobVersion,
            )
        )
        self.arq = life_cycle.ARQClient(
            self.config_redis, life_cycle.AsyncSleep, life_cycle.Pool
        )
        self.enqueue_gate = life_cycle.EnqueueGate

    async def _db_startup(self, ctx, db_startup_ctx: DBStartUpContext) -> None:
        db = Engine(db_startup_ctx)
        await db.startup()
        async with db.client() as conn:
            row = await conn.fetchrow("select true as check")
        if row["check"] is not True:
            raise RuntimeError("DB probe failed (unexpected result)")
        ctx["db"] = db

    async def db_shutdown(self, ctx) -> None:
        """Shutdown the db before worker shutdown"""
        await ctx["db"].shutdown()

    def settings(self) -> RedisSettings:
        """Redis Connection setting used by worker"""
        return RedisSettings(
            host=self.config_redis.Host,
            port=self.config_redis.Port,
        )

    async def start_all(self, ctx) -> None:
        """Start up and create global context for the worker"""
        ctx["arq_client"] = self.arq
        await ctx["arq_client"].startup()
        ctx["log"] = Writer(self.config_log)
        ctx["config_log"] = self.config_log
        ctx["log_error_helper"] = Error()
        ctx["asubprocess"] = self.life_cycle.SubProcess
        ctx["data_dir"] = self.config_worker.DataDir
        ctx["asleep"] = self.life_cycle.AsyncSleep
        ctx["config_worker"] = self.config_worker
        ctx["reader"] = self.reader
        ctx["enqueue_gate"] = self.enqueue_gate

        db_startup_ctx = DBStartUpContext(
            Log=ctx["log"],
            UserContext=UserContext.DATA,
            Config=ctx["config_log"],
            LogErrorHelper=ctx["log_error_helper"],
            DBMaxPool=self.config_worker.DBMaxPool,
        )
        await self._db_startup(ctx, db_startup_ctx)
