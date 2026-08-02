from datetime import timedelta
from taskiq import TaskiqState
from shared.models.worker import JobConfig


class Client:

    def __init__(self, context: TaskiqState):
        self.context = context.state

    async def enqueue(self, request: JobConfig):
        """Enqueue a job
        - check gate for maintenance
        - configure queue resource by type and job id
        - enqeue with or with out a delay
        """
        if self.context.enqueue_gate:
            raise RuntimeError("Enqueue Gate Closed For Maintenance")
        queue = (
            self.context.queue.task_by_name(request.Type)
            .kicker()
            .with_labels(job_id=request.Id)
        )
        if request.Delay is not None:
            return await queue.schedule_by_interval(
                self.context.delay_source,
                timedelta(seconds=request.Delay),
                config=request,
            )
        return await queue.kiq(config=request)
