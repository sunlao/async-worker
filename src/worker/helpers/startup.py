from asyncio import gather
from typing import Tuple, Sequence
from worker.enqueuer.route import Route
from shared.models.constants import Audit, JobTypes, TargetTypes
from shared.models.worker import JobConfig


class Startup:
    def __init__(self, ctx):
        self.ctx = ctx
        self.reader = ctx["reader"]
        self.db = ctx["db"]

    async def _audit_detail(self, job_config: JobConfig) -> Tuple[str, Audit]:
        """Return (target, Audit) for a single job."""
        cfg = job_config.Config
        trg = cfg.Target
        sql = "select sys_source_hash, sys_job_id from raw.audit_dtl($1)"
        if cfg.TargetType != TargetTypes.PG:
            return trg, Audit(None)
        async with self.db.client() as conn:
            row = await conn.fetchrow(sql, trg)
        if row is None:
            return trg, Audit(None)
        return trg, Audit(row["sys_source_hash"].hex())

    async def _audit_details(self, configs: Sequence[JobConfig]) -> dict[str, Audit]:
        return dict(await gather(*[self._audit_detail(c) for c in configs]))

    async def updt_config(
        self, config: JobConfig, details: dict[str, Audit]
    ) -> JobConfig:
        cfg = config.Config
        detail = details[cfg.Target]
        cfg_updt = cfg.model_copy(update={"LastHash": detail.last_hash})
        return config.model_copy(update={"Config": cfg_updt})

    async def _enqueue_all(self, job_type: JobTypes) -> list:
        configs = self.reader.startup_configs(job_type)
        if job_type == JobTypes.MOVEMENT:
            audit_details = await self._audit_details(configs)
            new_configs = [await self.updt_config(c, audit_details) for c in configs]
        else:
            new_configs = configs
        enq = Route(self.ctx)
        return await gather(*[enq.execute(False, job_type, c) for c in new_configs])

    async def enqueue(self, job_type: JobTypes) -> list:
        return await self._enqueue_all(job_type)
