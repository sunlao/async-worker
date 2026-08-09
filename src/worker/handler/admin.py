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
    HandleExecution,
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

    async def _execution(self, job: JobConfig[AdminConfig]) -> HandleExecution:
        error_flag = False
        trace_back_nfo = None
        job_event_dto = None
        config: ExecutionConfig[AdminConfig] = ExecutionConfig(
            JobId=job.Id,
            JobConfig=job.Config,
            Start=self.start,
            StartCounter=self.start_counter,
        )
        try:
            job_event_dto = await Controller(self.context).execute(
                config, **dict(job.KWARGS)
            )
        except Exception as e:  # pylint: disable=broad-except
            error_flag = True
            trace_back_nfo = self.context["log_error_helper"].trace_back_nfo(e)
        results: HandleExecution[AdminEvent] = HandleExecution(
            Event=job_event_dto, ErrorFlag=error_flag, TraceBackEvent=trace_back_nfo
        )
        return results

    def _log_error(
        self, job: JobConfig[AdminConfig], results: HandleExecution
    ) -> EventError:
        core_msg = f"Failed to execute {job.Config.Name} Job"
        core = core_log(
            self.context["config_log"], LogLevel.ERROR, Events.HANDLER, core_msg
        )
        error_result = AdminJobResult(Pass=False)
        event_dto = AdminEvent(
            JobId=job.Id,
            JobName=job.Config.Name,
            ConnectionProfile=job.Config.ConnectionProfile,
            Key=job.Config.Key,
            Status=False,
            Result=error_result,
            Message="Admin Handler",
            Start=self.start,
            End=self.config_log.Now(UTC),
            DurationMs=int((self.config_log.TimeCounter() - self.start_counter) * 1000),
        )
        dto: EventError[AdminEvent] = EventError(
            Core=core, Event=event_dto, Error=results.TraceBackEvent
        )
        self.context["log"].write_event_error(dto)
        return dto

    def _log(self, results: HandleExecution, job: JobConfig[AdminConfig]) -> Event:
        msg = f"Execute Job: {job.Config.Name}"
        core = core_log(self.config_log, LogLevel.INFO, Events.HANDLER, msg)
        dto: Event[AdminEvent] = Event(Core=core, Event=results.Event)
        self.context["log"].write_event(dto)
        return dto

    async def handle(self, job: JobConfig[AdminConfig]):
        """Handle movement job types"""
        results = await self._execution(job)
        if results.ErrorFlag:
            dto_error = self._log_error(job, results)
            return dto_error
        try:
            dto = self._log(results, job)
        except Exception as e:  # pylint: disable=broad-except
            core_msg = "Handler execution failed"
            trace_back_nfo = self.context["log_error_helper"].trace_back_nfo(e)
            raise RuntimeError(f"{core_msg}: {trace_back_nfo}")
        return dto
