from datetime import UTC
from datetime import timedelta, datetime
from taskiq import TaskiqState
from shared.log.helpers.core import build as core_log
from shared.models.constants import EnqueueTypes, Events, LogLevel
from shared.models.log import Event, EnqueueEvent
from shared.models.worker import JobConfig, EnqueueResponse, ReportState
from worker.core.extensions.enqueue import Enqueue


class Client:
    """Client for operating on the worker's queue
    - check gate for maintenance at instantiation
    - enqueue joob
    """

    def __init__(self, context: TaskiqState):
        self.context = context
        self.config_log = context["config_log"]
        self.tx_id = self.config_log.UUID4()
        self.start_counter = self.config_log.TimeCounter()
        self.start = self.config_log.Now(UTC)
        self.redis = context.redis_client
        self.pre_enqueue = Enqueue(context.redis_client)
        self.stream = context.queue.queue_name
        self.group = context.queue.consumer_group_name

    async def _exe_delay(
        self, request: JobConfig, enqueue_type: EnqueueTypes, queue, delay, core
    ):
        schedule_id = self.context.queue.id_generator()
        await self.pre_enqueue.claim(request.Id, schedule_id)
        try:
            response = await queue.with_schedule_id(schedule_id).schedule_by_time(
                self.context.delay_source,
                self.config_log.Now(UTC) + timedelta(seconds=delay),
                config=request,
            )
        except Exception:  # pylint: disable=broad-exception-caught
            await self.pre_enqueue.release_on_error(request.Id, schedule_id)
            raise
        event = EnqueueEvent(
            JobId=request.Id,
            JobType=request.Type,
            EnqueueType=enqueue_type,
            DelayId=response.schedule_id,
        )
        dto: Event[EnqueueEvent] = Event(Core=core, Event=event)
        self.context["log"].write_event(dto)
        return EnqueueResponse(JobId=request.Id, DelayId=response.schedule_id)

    async def _exe_run(
        self, request: JobConfig, enqueue_type: EnqueueTypes, queue, core
    ):
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

    @staticmethod
    def _delay(
        job_delay: int | None = None, delay_overide: int | None = None
    ) -> int | None:
        if delay_overide == 0:
            return None
        if delay_overide is not None:
            return delay_overide
        return job_delay

    @staticmethod
    def _text(value: str | bytes) -> str:
        return value.decode() if isinstance(value, bytes) else value

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
        if self.context.enqueue_gate is True:
            raise RuntimeError("Enqueue Gate Closed For Maintenance")
        queue = (
            self.context.queue.find_task(request.Type)
            .kicker()
            .with_labels(job_id=request.Id)
        )
        core_msg = f"Enqueue Job Id: {request.Id} with Job Type: {request.Type} "
        core = core_log(
            self.context["config_log"], LogLevel.INFO, Events.ENQUEUE, core_msg
        )
        delay = self._delay(request.Config.Delay, delay_overide)
        if delay is not None:
            return await self._exe_delay(request, enqueue_type, queue, delay, core)
        return await self._exe_run(request, enqueue_type, queue, core)

    async def redis_ping(self) -> bool:
        return await self.redis.ping()

    async def health(self) -> bool:
        heartbeat = await self.redis.get("awork-worker-heartbeat")
        if heartbeat is None:
            return False
        timestamp = datetime.fromisoformat(self._text(heartbeat))
        return self.config_log.Now(UTC) - timestamp <= timedelta(minutes=2)

    async def state(self) -> ReportState:
        delayed = 0
        async for key in self.redis.scan_iter(match="schedule:time:*"):
            delayed += await self.redis.llen(key)
        groups = await self.redis.xinfo_groups(self.stream)
        group = next(item for item in groups if self._text(item["name"]) == self.group)
        in_flight = group["pending"]
        entries_read = group["entries-read"] or 0
        return ReportState(
            Delayed=delayed,
            Enqueued=group["lag"],
            InFlight=in_flight,
            Acknowledged=entries_read - in_flight,
        )
