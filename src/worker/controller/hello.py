from datetime import UTC
from worker.connector.io.connector import Connector as CLI
from worker.connector.api.connector import Connector as API
from worker.connector.db.connector import Connector as DB
from shared.models.constants import ConnectorTypes, ResourceTypes
from shared.models.worker import (
    HelloEvent,
    ExecutionConfig,
    HelloConfig,
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
        if prof.ResourceType == ResourceTypes.DB_POOL:
            return await DB(self.context).execute_db_pool(exe, prof, **kwargs)
        raise RuntimeError(f"Undefined ResourceType: {prof.ResourceType}")

    async def _io_actions(
        self, exe: ExecutionConfig[HelloConfig], prof: ConnectionProfile, **kwargs
    ):
        pass

    def _event(
        self, exe: ExecutionConfig[HelloConfig], msg: str, result: HelloJobResult
    ) -> HelloEvent:
        return HelloEvent(
            JobId=exe.JobId,
            JobName=exe.JobConfig.Name,
            ConnectionProfile=exe.JobConfig.ConnectionProfile,
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
            result = await self._db_actions(exe, profile, **kwargs)
        if connector_type == ConnectorTypes.IO:
            result = await self._io_actions(exe, profile, **kwargs)
        if connector_type == ConnectorTypes.API:
            result = await self._api_actions(exe, profile, **kwargs)
        result = HelloJobResult(Pass=True)
        return self._event(exe, "g2g", result)
