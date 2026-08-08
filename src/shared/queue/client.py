from datetime import UTC
from datetime import timedelta
from taskiq import TaskiqState
from shared.log.helpers.core import build as core_log
from shared.models.constants import EnqueueTypes, Events, LogLevel
from shared.models.log import Event, EnqueueEvent
from shared.models.worker import JobConfig, EnqueueResponse


class Client:
    """Client for operating on the worker's queue
    - check gate for maintenance at instantiation
    - enqueue joob
    """

    def __init__(self, context: TaskiqState):
        self.context = context
        if self.context.enqueue_gate:
            raise RuntimeError("Enqueue Gate Closed For Maintenance")
        self.config_log = context["config_log"]
        self.tx_id = self.config_log.UUID4()
        self.start_counter = self.config_log.TimeCounter()
        self.start = self.config_log.Now(UTC)

    @staticmethod
    def _delay(
        job_delay: int | None = None, delay_overide: int | None = None
    ) -> int | None:
        if delay_overide == 0:
            return None
        if delay_overide is not None:
            return delay_overide
        return job_delay

    async def enqueue(
        self,
        request: JobConfig,
        enqueue_type: EnqueueTypes,
        delay_overide: int | None = None,
    ):
        """Enqueue operations
        - configure queue resource by type and job id
        - enqueue with or with out a delay
          - Use delay overide if exists
          - Use job config delay if exists and delay overide is none
        """
        queue = (
            self.context.queue.find_task(request.Type)
            .kicker()
            .with_labels(job_id=request.Id)
        )
        core_msg = f"Enqueue Job Id: {request.Id} with Job Type: {request.Type} "
        core = core_log(
            self.coenqueuentext["config_log"], LogLevel.INFO, Events.ENQUEUE, core_msg
        )
        delay = self._delay(request.Config.Delay, delay_overide)
        if delay is not None:
            response = await queue.schedule_by_interval(
                self.context.delay_source,
                timedelta(seconds=delay),
                config=request,
            )
            event = EnqueueEvent(
                JobId=request.Id,
                JobType=request.Type,
                EnqueueType=enqueue_type,
                DelayId=response.schedule_id,
            )
            dto: Event[EnqueueEvent] = Event(Core=core, Event=event)
            self.context["log"].write_event(dto)
            return EnqueueResponse(JobId=request.Id, DelayId=response.schedule_id)
        response = await queue.kiq(config=request)
        event = EnqueueEvent(
            JobId=request.Id,
            JobType=request.Type,
            EnqueueType=enqueue_type,
            RunId=response.task_id,
        )
        dto: Event[EnqueueEvent] = Event(Core=core, Event=event)
        self.context["log"].write_event(dto)
        return EnqueueResponse(JobId=request.Id, RunId=response.task_id)
