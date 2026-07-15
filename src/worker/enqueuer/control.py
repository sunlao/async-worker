from datetime import timedelta
from worker.enqueuer.helper import delay
from shared.models.api import EnqueueResponse
from shared.models.constants import JobTypes, TargetTypes
from shared.models.worker import EnqueueRequest, JobConfig, MovementJobResult


class Control:
    def __init__(self, ctx):
        self.arq = ctx["arq_client"]
        self.gate = ctx["enqueue_gate"]
        self.run_id = ctx.get("job_id")

    def _update_config(
        self, re_enqueue: bool, config: JobConfig, result: MovementJobResult = None
    ):
        if re_enqueue is False:
            return config
        last_hash = result.LastHash
        updt = config.Config.model_copy(update={"LastHash": last_hash})
        return config.model_copy(update={"Config": updt})

    async def _exe_job(self, re_enqueue: bool, job_type: JobTypes, job_info: JobConfig):
        re_enqueue_id = self.run_id if re_enqueue is True else None
        run_result = await self.arq.enqueue(
            EnqueueRequest(
                JobType=job_type,
                Job=job_info,
                EnqueueGate=self.gate,
                DeferBy=timedelta(seconds=delay(re_enqueue, job_info, job_type)),
                ReEnqueue=re_enqueue,
                ReEnqueueId=re_enqueue_id,
            )
        )
        return run_result

    async def enqueue(
        self,
        re_enqueue: bool,
        job_type: JobTypes,
        job_info: JobConfig,
        target_result: MovementJobResult = None,
    ) -> EnqueueResponse:
        target_type = getattr(job_info.Config, "TargetType", "n/a")
        if job_type == JobTypes.MOVEMENT and target_type not in (TargetTypes.PG):
            job_info = self._update_config(re_enqueue, job_info, target_result)
        job = await self._exe_job(re_enqueue, job_type, job_info)
        if re_enqueue is True and job is None:
            msg = (
                "ReEnqueue failed. Job enqueued with a run id that does not match "
                "ReEnqueueId"
            )
            return EnqueueResponse(RunID="n/a", Message=msg, Status="n/a")
        if job is None:
            msg = f"Enqueue failed. Job Id: {job_info.Config.Id} already enqueued"
            return EnqueueResponse(RunID="n/a", Message=msg, Status="n/a")
        status = await job.status()
        if re_enqueue is False:
            return EnqueueResponse(
                RunID=job.job_id,
                Message=f"{job_type} Enqueued for job {job_info.Config.Id}",
                Status=status,
            )
        return EnqueueResponse(
            RunID=job.job_id,
            Message=f"{job_type} Re-enqueued for job {job_info.Config.Id}",
            Status=status,
        )
