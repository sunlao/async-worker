from taskiq import TaskiqState
from shared.models.worker import EnqueueRequest


class Client:
    def __init__(self, state: TaskiqState) -> None:
        self.state = state

    async def enqueue(self, request: EnqueueRequest):
        if request.EnqueueGate:
            raise RuntimeError("Enqueue Gate Closed")
        dispatcher = self.state.queue.task_by_name(request.JobType)

        await dispatcher.kicker().with_labels(job_id=request.Job.Config.Id).kiq(
            request.Job
        )
