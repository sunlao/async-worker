from datetime import timedelta
from shared.models.worker import EnqueueRequest


class Client:
    async def enqueue(self, request: EnqueueRequest):
        if request.WorkerState.enqueue_gate:
            raise RuntimeError("Enqueue Gate Closed")
        queue = (
            request.WorkerState.queue
            .task_by_name(request.JobConfig.Type)
            .kicker().with_labels(job_id=request.JobId)
        )
        if request.Delay is not None:
            return await queue.schedule_by_interval(
                request.WorkerState.delay_source,
                timedelta(seconds=request.Delay),
                job=request.JobConfig,
            )
        return await queue.kiq(job=request.JobConfig)
