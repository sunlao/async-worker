from datetime import UTC
from shared.models.constants import ActionTypes, ConnectorTypes, ResourceTypes
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
    ) -> AdminJobResult:
        if prof.ResourceType != ResourceTypes.REDIS_CLIENT:
            raise RuntimeError(f"Undefined ResourceType: {prof.ResourceType}")
        if exe.JobConfig.ActionType == ActionTypes.SET:
            if exe.JobConfig.Key is None:
                raise RuntimeError("Key is required for SET")
            result = await Redis(self.context).upsert(
                exe.JobConfig.Key, self.log.Now(UTC).isoformat()
            )
            return AdminJobResult(Pass=result)
        else:
            raise RuntimeError(f"Unsupported ActionType: {exe.JobConfig.ActionType}")

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

    async def execute(self, exe: ExecutionConfig[AdminConfig], **kwargs) -> AdminEvent:
        """Controller to execute Admin jobs Action Types by controller"""
        profile = self.connection.profile(exe.JobConfig.ConnectionProfile)
        connector_type = profile.ConnectorType
        if connector_type == ConnectorTypes.DB:
            result = await self._db_actions(exe, profile)
        else:
            raise RuntimeError(f"Unsupported ConnectorTypes: {connector_type}")
        await self.post_process.execute(exe.JobId)
        return self._event(exe, "g2g", result)
