from datetime import UTC
from worker.connector.io.connector import Connector as CLI
from worker.connector.api.connector import Connector as API
from worker.connector.db.pool import Pool
from shared.models.constants import ConnectorTypes, ResourceTypes
from shared.models.worker import (
    HelloEvent,
    ExecutionConfig,
    HelloConfig,
    HelloJobResult,
    ConnectionProfile,
    ConnecterDBPoolInput,
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
        self, exe: ExecutionConfig[HelloConfig], prof: ConnectionProfile
    ):
        pass_args = {}
        if prof.ResourceType == ResourceTypes.DB_EDGE:
            queries = exe.JobConfig.Queries
            for q in queries:
                input = ConnecterDBPoolInput(
                    ActionType=q.ActionType, SQLName=q.Name, ARGS=q.Args
                )
                print(f"name: {q.Name}")
                print(f"q: {q.PassResultFlag}")
                row = await Pool(self.context).execute(input, **pass_args)
                print(f"row: {row}")
            return True
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
            result1 = await self._db_actions(exe, profile)
        if connector_type == ConnectorTypes.IO:
            result2 = await self._io_actions(exe, profile, **kwargs)
        if connector_type == ConnectorTypes.API:
            result3 = await self._api_actions(exe, profile, **kwargs)
        result = HelloJobResult(Pass=True)
        return self._event(exe, "g2g", result)
