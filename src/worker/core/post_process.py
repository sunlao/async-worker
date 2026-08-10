from taskiq import TaskiqState
from shared.models.constants import EnqueueTypes
from shared.models.worker import EnqueueResponse
from worker.client import Client


class PostProcess:
    """Enqueue jobs that follow a completed job."""

    def __init__(self, context: TaskiqState):
        self.job = context.job
        self.gather = context.gather
        self.client = Client(context)

    async def _enqueue(self, job_id: int, type: EnqueueTypes) -> EnqueueResponse:
        job = self.job.config(job_id)
        return await self.client.enqueue(job, type)

    async def execute(self, job_id: int) -> list[EnqueueResponse] | None:
        enqueue_info = []
        job = self.job.config(job_id)
        if job.Config.RunOnce is False:
            enqueue_info.append((job.Id, EnqueueTypes.REENQUEUE))
        for i in job.Config.RunNext:
            enqueue_info.append((i, EnqueueTypes.NEXT))
        if len(enqueue_info) == 0:
            return None
        return await self.gather(
            *(self._enqueue(id, type) for id, type in enqueue_info)
        )