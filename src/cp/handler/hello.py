# pylint: disable=duplicate-code
from datetime import UTC
from taskiq import TaskiqState
from worker.controller.movement import Movement as Controller
from shared.log.helpers.core import build as core_log
from shared.models.constants import Events, LogLevel
from shared.models.log import Event, EventError
from shared.models.worker import (
    ExecutionConfig,
    JobConfig,
    HelloConfig,
    MovementEvent,
    HandleExecution,
    MovementJobResult,
    ActionTypes,
)


class Hello:
    """Hello Handler executes Controller and Logs"""

    def __init__(self, context: TaskiqState):
        self.context = context
        self.config_log = context["config_log"]
        self.tx_id = self.config_log.UUID4()
        self.start_counter = self.config_log.TimeCounter()
        self.start = self.config_log.Now(UTC)

    async def _execution(self, config_job: MovementConfig, **kwargs) -> HandleExecution:
        error_flag = False
        trace_back_nfo = None
        job_event_dto = None
        config: ExecutionConfig[MovementConfig] = ExecutionConfig(
            JobConfig=config_job, Start=self.start, StartCounter=self.start_counter
        )
        try:
            async with self.context["db"].client() as conn:
                job_event_dto = await Controller(self.context, conn).execute(
                    config, **kwargs
                )
        except Exception as e:  # pylint: disable=broad-except
            error_flag = True
            trace_back_nfo = self.context["log_error_helper"].trace_back_nfo(e)
        results: HandleExecution[MovementEvent] = HandleExecution(
            Event=job_event_dto, ErrorFlag=error_flag, TraceBackEvent=trace_back_nfo
        )
        return results

    def _log_error(
        self, config_job: MovementConfig, results: HandleExecution
    ) -> EventError:
        core_msg = (f"Failed to execute {config_job.Name} Job",)
        core = core_log(
            self.context["config_log"], LogLevel.ERROR, Events.JOB, core_msg
        )
        error_result = MovementJobResult(ActionType=ActionTypes.NA, RowCount=0)
        event_dto = MovementEvent(
            JobId=config_job.Id,
            JobName=config_job.Name,
            Source=config_job.Source,
            Status=False,
            Result=error_result,
            Message="Movement Handler",
            Start=self.start,
            End=self.config_log.Now(UTC),
            DurationMs=int((self.config_log.TimeCounter() - self.start_counter) * 1000),
        )
        dto: EventError[MovementEvent] = EventError(
            Core=core, Event=event_dto, Error=results.TraceBackEvent
        )
        self.context["log"].write_event_error(dto)
        return dto

    def _log(self, results: HandleExecution, config_job: MovementConfig) -> Event:
        msg = f"Execute Job: {config_job.Name}"
        core = core_log(self.config_log, LogLevel.INFO, Events.JOB, msg)
        dto: Event[MovementEvent] = Event(Core=core, Event=results.Event)
        self.context["log"].write_event(dto)
        return dto

    async def handle(self, config_job: JobConfig[HelloConfig]):
        """Handle movement job types"""
        results = await self._execution(config_job)
        if results.ErrorFlag:
            dto_error = self._log_error(config_job, results)
            return dto_error
        dto = self._log(results, config_job)
        return dto
