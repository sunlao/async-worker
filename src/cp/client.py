from datetime import timedelta
from taskiq import TaskiqState
from shared.models.worker import JobConfig, EnqueueResponse


class Client:
    """Client for operating on queue
    - check gate for maintenance at instantiation
    """

    def __init__(self, context: TaskiqState):
        self.context = context
        if self.context.enqueue_gate:
            raise RuntimeError("Enqueue Gate Closed For Maintenance")

    @staticmethod
    def _delay(
        job_delay: int | None = None, delay_overide: int | None = None
    ) -> int | None:
        if delay_overide is not None:
            return delay_overide
        return job_delay

    async def enqueue(self, request: JobConfig, delay_overide: int | None = None):
        """Enquue operations
        - configure queue resource by type and job id
        - enqeue with or with out a delay
          - Use delay overide if exists
          - Use job config delay if exists and delay overide is none
        """
        queue = (
            self.context.queue.task_by_name(request.Type)
            .kicker()
            .with_labels(job_id=request.Id)
        )
        delay = self._delay(request.Config.Delay, delay_overide)
        if delay is not None:
            response = await queue.schedule_by_interval(
                self.context.delay_source,
                timedelta(seconds=delay),
                config=request,
            )
            return EnqueueResponse(JobId=request.Id, DelayId=response.schedule_id)
        response = await queue.kiq(config=request)
        return EnqueueResponse(JobId=request.Id, RunId=response.task_id)
