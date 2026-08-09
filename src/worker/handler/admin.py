# pylint: disable=duplicate-code
from datetime import UTC
from taskiq import TaskiqState
from worker.controller.admin import Admin as Controller
from shared.log.helpers.core import build as core_log
from shared.models.constants import Events, LogLevel
from shared.models.log import Event, EventError
from shared.models.worker import (
    ExecutionConfig,
    JobConfig,
    AdminConfig,
    AdminEvent,
    AdminJobResult,
)


class Admin:
    """Admin Handler executes Controller and Logs"""

    def __init__(self, context: TaskiqState):
        self.context = context
        self.config_log = context["config_log"]
        self.tx_id = self.config_log.UUID4()
        self.start_counter = self.config_log.TimeCounter()
        self.start = self.config_log.Now(UTC)

    async def _execution(self, job: JobConfig[AdminConfig]) -> AdminEvent:
        config: ExecutionConfig[AdminConfig] = ExecutionConfig(
            JobId=job.Id,
            JobConfig=job.Config,
            Start=self.start,
            StartCounter=self.start_counter,
        )
        return await Controller(self.context).execute(config)

    def _log_error(self, job: JobConfig[AdminConfig], error: Exception) -> EventError:
        core_msg = f"Failed to execute {job.Config.Name} Job"
        core = core_log(self.config_log, LogLevel.ERROR, Events.HANDLER, core_msg)
        result = AdminJobResult(Pass=False, Message="Handler Failed")
        event_dto = AdminEvent(
            JobId=job.Id,
            JobName=job.Config.Name,
            ConnectionProfile=job.Config.ConnectionProfile,
            Key=job.Config.Key,
            Status=False,
            Result=result,
            Message="Admin Handler",
            Start=self.start,
            End=self.config_log.Now(UTC),
            DurationMs=int((self.config_log.TimeCounter() - self.start_counter) * 1000),
        )
        dto: EventError[AdminEvent] = EventError(
            Core=core,
            Event=event_dto,
            Error=self.context["log_error_helper"].trace_back_nfo(error),
        )
        self.context["log"].write_event_error(dto)
        return dto

    def _log(self, result: AdminEvent, job: JobConfig[AdminConfig]) -> Event:
        msg = f"Execute Job: {job.Config.Name}"
        core = core_log(self.config_log, LogLevel.INFO, Events.HANDLER, msg)
        dto: Event[AdminEvent] = Event(Core=core, Event=result)
        self.context["log"].write_event(dto)
        return dto

    async def handle(self, job: JobConfig[AdminConfig]):
        """Handle admin job types"""
        try:
            result = await self._execution(job)
        except Exception as error:
            self._log_error(job, error)
            raise
        return self._log(result, job)
