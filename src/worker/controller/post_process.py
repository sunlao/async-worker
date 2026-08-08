from taskiq import TaskiqState
from shared.models.worker import EnqueueResponse
from shared.queue.client import Client


class PostProcess:
    """Enqueue jobs that follow a completed job."""

    def __init__(self, context: TaskiqState):
        self.job = context.job
        self.gather = context.gather
        self.client = Client(context)

    async def _enqueue(self, job_id: int) -> EnqueueResponse:
        job = self.job.config(job_id)
        return await self.client.enqueue(job)

    async def execute(self, job_id: int) -> list[EnqueueResponse] | None:
        job_ids = []
        job = self.job.config(job_id)
        if job.Config.RunOnce is False:
            job_ids.append(job.Id)
        for i in job.Config.RunNext:
            job_ids.append(i)
        if len(job_ids) == 0:
            return None
        return await self.gather(*(self._enqueue(i) for i in job_ids))
