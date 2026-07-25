from re import findall
from datetime import datetime
from contextlib import asynccontextmanager
from typing import AsyncIterator
from arq.connections import RedisSettings
from arq.jobs import Job as ARQ_Job, JobDef
from shared.queue.ledger_data import serialize
from shared.models.api import LedgerData
from shared.models.worker import EnqueueRequest, Health


class Client:
    """Shared Light weight ARQ client for api and worker services"""

    def __init__(self, redis_config, async_sleep, create_pool) -> None:
        self.config = redis_config
        self.sleep = async_sleep
        self.create_pool = create_pool
        self.pool = None

    async def completed(self):
        """All completed jobs with results"""
        return await self.pool.all_job_results()

    async def delete(self):
        keys = await self.pool.keys("arq:*")
        if keys:
            await self.pool.delete(*keys)

    async def delete_by_job_id(self, job_id: int):
        """This is only used to support testing"""
        q = await self.queued(job_id)
        q_run_ids = [run_info.job_id for run_info in q]
        c = await self.completed()
        c_run_ids = [run.job_id for run in c if run.args[0].Config.Id == job_id]
        run_ids = q_run_ids + c_run_ids
        deleted = 0
        for run_id in run_ids:
            patterns = [
                f"arq:queue:{run_id}*",
                f"arq:in-progress:{run_id}*",
                f"arq:result:{run_id}*",
            ]
            for pattern in patterns:
                keys = await self.pool.keys(pattern)
                if keys:
                    await self.pool.delete(*keys)
                    deleted += len(keys)
        return deleted

    async def enqueue(self, request: EnqueueRequest) -> str:
        if request.EnqueueGate is True:
            raise RuntimeError("Enqueue Gate Closed")
        q = await self.queued(request.Job.Config.Id)
        if request.ReEnqueue is False and len(q) == 0:
            job = await self.pool.enqueue_job(
                request.JobType,
                request.Job,
                _defer_by=request.DeferBy,
            )
            return job
        q_cnt = len(q)
        run_ids = [run_info.job_id for run_info in q]
        if request.ReEnqueue is True and q_cnt == 1 and request.ReEnqueueId in run_ids:
            q_cnt = len(q)
            job = await self.pool.enqueue_job(
                request.JobType,
                request.Job,
                _defer_by=request.DeferBy,
            )
            return job
        return None

    async def flush(self) -> None:
        """Support CI pipelines with a flush job for code coverage
        - executing in any evironment besides ci does nothing"""
        await self.pool.enqueue_job("flush")

    async def health(self) -> Health:
        raw = await self.pool.get("arq:queue:health-check")
        if not raw:
            return Health(Complete=-1, Failed=-1, Retried=-1, Ongoing=-1, Queued=-1)
        text = raw.decode() if isinstance(raw, bytes) else str(raw)
        health = {k: int(v) for k, v in findall(r"(\w+)=(\d+)", text)}
        return Health(
            Complete=health["j_complete"],
            Failed=health["j_failed"],
            Retried=health["j_retried"],
            Ongoing=health["j_ongoing"],
            Queued=health["queued"],
        )

    async def ledger(self, max_ledger_date: datetime) -> tuple[LedgerData, ...]:
        ledger = [serialize(job) for job in await self.completed()]
        return {i for i in ledger if i.FinishTime > max_ledger_date}

    # pylint: disable=protected-access
    async def queued(self, job_id: int | None = None) -> list[JobDef]:
        """returns a list of queued jobs definitions that doesn't blow up
        when job_def not found"""
        queue_name = self.pool.default_queue_name
        runs = await self.pool.zrange(queue_name, 0, -1, withscores=True)
        job_defs = []
        for run_id, score in runs:
            try:
                job_def = await self.pool._get_job_def(run_id, int(score))
                if job_id is None or job_def.args[0].Config.Id == job_id:
                    job_defs.append(job_def)
            except RuntimeError as e:
                if "not found" in str(e):
                    continue
                raise
        return job_defs

    async def redis_ping(self) -> bool:
        """Ping ARQ worker's Redis queue"""
        attempts = self.config.RedisPingAttempts
        delay_s = self.config.RedisPingDelaySec
        for _ in range(attempts):
            try:
                pong = await self.pool.ping()
                if pong:
                    return True
            except Exception:  # pylint: disable=broad-except
                await self.sleep(delay_s)
        return False

    # Job construction is synchronous
    def run_info(self, run_id) -> ARQ_Job:
        """Return ARQ jobs Object"""
        return ARQ_Job(run_id, redis=self.pool)

    async def shutdown(self) -> None:
        if self.pool and hasattr(self.pool, "close"):
            await self.pool.close()
        self.pool = None

    async def startup(self) -> None:
        host = f"{self.config.AppCode}-redis"
        self.pool = await self.create_pool(
            RedisSettings(host=host, port=self.config.Port)
        )

    @asynccontextmanager
    async def client(self) -> AsyncIterator:
        try:
            yield self.pool
        finally:
            pass
