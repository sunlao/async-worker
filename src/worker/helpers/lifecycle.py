from shared.config.reader import Reader
from shared.db import Engine
from shared.log.writer import Writer
from shared.log.helpers.error import Error
from shared.models.config import ReaderConfig, Redis
from shared.models.constants import UserContext
from shared.models.db import DBStartUpContext
from shared.models.worker import Lifecycle


# pylint: disable=too-many-instance-attributes
class LifeCycle:
    """Utility to set queue lifecyle"""

    def __init__(self, life_cycle: Lifecycle):
        self.life_cycle = life_cycle
        self.locker = life_cycle.Locker
        config_redis = self.locker.redis()
        self.config_log = self.locker.log()
        self.config_worker = self.locker.worker()
        self.reader = Reader(
            ReaderConfig(
                JobPath=self.config_worker.JobPath,
                JobVersion=self.config_worker.JobVersion,
            )
        )
        self.enqueue_gate = life_cycle.EnqueueGate
        self.broker = self._broker(config_redis, life_cycle)

    def _broker(self, config_redis: Redis, life_cycle: Lifecycle):
        redis_url = f"redis://{config_redis.Host}:{config_redis.Port}"
        backend = life_cycle.Backend(redis_url=redis_url,result_ex_time=14400)
        return life_cycle.Broker(url=redis_url).with_result_backend(backend)

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

    async def start_all(self, ctx) -> None:
        """Start up and create global context for the worker"""
        ctx["log"] = Writer(self.config_log)
        ctx["config_log"] = self.config_log
        ctx["log_error_helper"] = Error()
        ctx["asubprocess"] = self.life_cycle.SubProcess
        ctx["data_dir"] = self.config_worker.DataDir
        ctx["asleep"] = self.life_cycle.AsyncSleep
        ctx["config_worker"] = self.config_worker
        ctx["reader"] = self.reader
        ctx["enqueue_gate"] = self.enqueue_gate
        ctx["broker"] = self.broker

        db_startup_ctx = DBStartUpContext(
            Log=ctx["log"],
            UserContext=UserContext.DATA,
            Config=ctx["config_log"],
            LogErrorHelper=ctx["log_error_helper"],
            DBMaxPool=self.config_worker.DBMaxPool,
        )
        await self._db_startup(ctx, db_startup_ctx)
