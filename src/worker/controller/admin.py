from datetime import UTC
from shared.models.constants import ConnectorTypes, ResourceTypes
from shared.models.worker import (
    AdminEvent,
    ExecutionConfig,
    AdminConfig,
    AdminJobResult,
    ConnectionProfile,
)
from worker.connector.db.redis import Redis
from worker.controller.post_process import PostProcess


class Admin:
    """Admin Controller - domain logic for admin job types
    - Heartbeat: provivde a single heartbeat KVP to support client observabilty Readiness checks
        - Key: Supplied by job config
        - Value: Now(UTC)
        - Delay: Supplied by job config
        - Client owns TTL chck: Pass if Now(UTC) is <= timestamp + Delay + 1 60 seconds
    - Support Ledger
        - TBD
    """

    def __init__(self, context):
        self.context = context
        self.log = self.context["config_log"]
        self.gate = context["enqueue_gate"]
        self.connection = context.connection
        self.post_process = PostProcess(self.context)


    async def _db_actions(
        self, exe: ExecutionConfig[AdminConfig], prof: ConnectionProfile
    ):
        if prof.ResourceType == ResourceTypes.REDIS_CLIENT:
            # TODO
            return AdminJobResult(Pass=False)
        raise RuntimeError(f"Undefined ResourceType: {prof.ResourceType}")

    def _event(
        self, exe: ExecutionConfig[AdminConfig], msg: str, result: AdminJobResult
    ) -> AdminEvent:
        return AdminEvent(
            JobId=exe.JobId,
            JobName=exe.JobConfig.Name,
            ConnectionProfile=exe.JobConfig.ConnectionProfile,
            Key=exe.JobConfig.Key,
            Status=True,
            Message=msg,
            Start=exe.Start,
            End=self.log.Now(UTC),
            DurationMs=int((self.log.TimeCounter() - exe.StartCounter) * 1000),
            Result=result,
        )

    @staticmethod
    def _pass_kwargs(result) -> tuple[object, ...]:
        return tuple(value for row in result for value in row)

    async def execute(self, exe: ExecutionConfig[AdminConfig], **kwargs) -> AdminEvent:
        """Controller to execute Admin jobs Action Types by controller"""
        profile = self.connection.profile(exe.JobConfig.ConnectionProfile)
        connector_type = profile.ConnectorType
        if connector_type == ConnectorTypes.DB:
            result = await self._db_actions(exe, profile)
        else:
            raise RuntimeError(f"Undefined ConnectorTypes: {connector_type}")
        await self.post_process.execute(exe.JobId)
        return self._event(exe, "g2g", result)
