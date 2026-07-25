from typing import Any
from shared.models.api import TargetAuditDetailResponse
from shared.models.worker import JobConfig, MovementConfig, TargetTypes


class TargetAuditDetail:
    """Help the api and worker with enqueuing movement jobs by consolidating facts
    from worker and target database if applicable.
    - Database targets have succesfull hash and sequence info that was persisted
    - Worker has all current run ids that are inflight and queued
    """

    def __init__(self, db):
        self.db = db

    async def _audit_detail(self, config: MovementConfig):
        """Get audit detail from target"""
        if config.TargetType in (TargetTypes.PG):
            db_dtl = await self._db_audit_detail(config.Target)
            return TargetAuditDetailResponse(Hash=db_dtl["hash"])
        return TargetAuditDetailResponse(Hash=None)

    async def _db_audit_detail(self, target: str) -> dict[str, Any]:
        sql = "select sys_source_hash from raw.audit_dtl($1)"
        async with self.db.client() as conn:
            row = await conn.fetchrow(sql, target)
        if row is None:
            return {"hash": None}
        return {"hash": row["sys_source_hash"].hex()}

    async def update_job(self, config: JobConfig) -> JobConfig:
        """Update movement config with audit detailfrom target"""
        dtl = await self._audit_detail(config.Config)
        new = config.Config.model_copy(update={"LastHash": dtl.Hash})
        return config.model_copy(update={"Config": new})
