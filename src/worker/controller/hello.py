from datetime import UTC
from worker.connector.io.connector import Connector as CLI
from worker.connector.api.connector import Connector as API
from shared.models.constants import JobTypes, ActionTypes, ConnectorTypes
from shared.models.worker import (
    HelloEvent,
    ExecutionConfig,
    HelloConfig,
    JobConfig,
    HelloJobResult,
    ConnectionProfile,
)


class HelloErrorHandling(Exception):
    def __init__(self, p_job_id):
        super().__init__(
            f"{p_job_id} failed as part of Hello Controller error handling"
        )


class Hello:
    """Hello Controller demonstrates worker functionality"""

    def __init__(self, context):
        self.context = context
        self.log = self.context["config_log"]
        self.gate = context["enqueue_gate"]
        self.connection = context.connection

    async def _api_actions(
        self, exe: ExecutionConfig[HelloConfig], prof: ConnectionProfile, **kwargs
    ):
        pass

    async def _db_actions(
        self, exe: ExecutionConfig[HelloConfig], prof: ConnectionProfile, **kwargs
    ):
        pass

    async def _io_actions(
        self, exe: ExecutionConfig[HelloConfig], prof: ConnectionProfile, **kwargs
    ):
        pass

    async def _enqueue(
        self,
        config_exe: ExecutionConfig[HelloConfig],
        msg: str,
        result: HelloJobResult,
        **kwargs,
    ) -> HelloEvent:
        config_job = config_exe.JobConfig
        dto = JobConfig(Type=JobTypes.MOVEMENT, Config=config_job, KWARGS=kwargs)
        enqueue = await Route(self.context).execute(True, JobTypes.MOVEMENT, dto, result)
        e_msg = f"{msg}" f" - {enqueue.Message} with status {enqueue.Status}"
        return self._event(config_exe, e_msg, result)

    def _event(
        self, exe: ExecutionConfig[HelloConfig], msg: str, result: HelloJobResult
    ) -> HelloEvent:
        return HelloEvent(
            JobId=exe.JobId,
            JobName=exe.JobConfig.Name,
            Target=exe.JobConfig.Target,
            Status=True,
            Message=msg,
            Start=exe.Start,
            End=self.log.Now(UTC),
            DurationMs=int((self.log.TimeCounter() - exe.StartCounter) * 1000),
            Result=result,
        )

    async def execute(self, exe: ExecutionConfig[HelloConfig], **kwargs) -> HelloEvent:
        """Controller to execute Hello jobs Action Types by controller"""
        profile = self.connection.profile(exe.JobConfig.ConnectionProfile)
        connector_type = profile.ConnectorType
        if connector_type == ConnectorTypes.DB:
            result = self._db_actions(exe, profile, **kwargs)
        if connector_type == ConnectorTypes.IO:
            result = self._io_actions(exe, profile, **kwargs)
        if connector_type == ConnectorTypes.API:
            result = self._api_actions(exe, profile, **kwargs)
        msg = "Movement Controller: Completed run"
        return await self._enqueue(exe, msg, result, **kwargs)
