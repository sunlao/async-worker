from shared.helper.target_audit_detail import TargetAuditDetail
from shared.models.api import EnqueueResponse
from shared.models.constants import JobTypes
from shared.models.worker import JobConfig, MovementJobResult
from worker.enqueuer.control import Control


class Route:
    """Used by worker Startup and Controllers to enqueue, re-enqueue and
    emit run next messages"""

    def __init__(self, ctx):
        self.control = Control(ctx)
        self.reader = ctx["reader"]
        self.tad = TargetAuditDetail(ctx["arq_client"], ctx["db"])

    async def _enqueue(
        self,
        re_enqueue: bool,
        job_type: JobTypes,
        enqueue_config: JobConfig,
        target_result: MovementJobResult = None,
    ) -> EnqueueResponse:
        """Enqueue and re-enqueue jobs"""
        if enqueue_config.Config.RunOnce is True and re_enqueue is True:
            msg = "Run Once Job: No re-enqueue"
            return EnqueueResponse(RunID="n/a", Message=msg, Status="ok")
        if job_type == JobTypes.MOVEMENT:
            updt = await self.tad.update_job(enqueue_config)
            return await self.control.enqueue(re_enqueue, job_type, updt, target_result)
        raise RuntimeError(f"Job Type: {job_type} - Not Supported ")

    async def _run_next(self, job_config: JobConfig):
        job_type = job_config.Type)
        if job_type == JobTypes.MOVEMENT:
            updt = await self.tad.update_job(job_config)
            await self.control.enqueue(False, job_type, updt)

    async def _run_next_all(self, run_next: list[int]):
        for job_id in run_next:
            await self._run_next(self.reader.config(job_id))

    async def execute(
        self,
        re_enqueue: bool,
        job_type: JobTypes,
        enqueue_config: JobConfig,
        target_result: MovementJobResult = None,
    ) -> EnqueueResponse:
        response = await self._enqueue(
            re_enqueue, job_type, enqueue_config, target_result
        )
        if enqueue_config.Config.RunNext and re_enqueue is True:
            await self._run_next_all(enqueue_config.Config.RunNext)
        return response
