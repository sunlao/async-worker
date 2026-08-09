from datetime import UTC
from shared.models.constants import ConnectorTypes, ResourceTypes
from shared.models.worker import (
    AdminEvent,
    ExecutionConfig,
    AdminConfig,
    AdminJobResult,
    ConnectionProfile,
    ConnecterDBPoolInput,
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

    @staticmethod
    def _db_check(check, result, name):
        if name == "admin_select_count_abc_canary" and result[0] == 1:
            check["abc"] = True
        if name == "admin_select_count_abc_def_canary" and result[0] == 2:
            check["abc_def"] = True
        return check

    async def _db_actions(
        self, exe: ExecutionConfig[AdminConfig], prof: ConnectionProfile
    ):
        if prof.ResourceType == ResourceTypes.REDIS_CLIENT:
            check = {"abc": False, "abc_def": False}
            queries = exe.JobConfig.Queries
            pass_kwargs = {}
            for q in queries:
                input = ConnecterDBPoolInput(
                    ActionType=q.ActionType, SQLName=q.Name, Args=q.Args
                )
                result = await Pool(self.context).execute(input, **pass_kwargs)
                check = self._db_check(check, result, q.Name)
                if q.PassResultFlag is True:
                    pass_kwargs = {"args_orveride": self._pass_kwargs(result)}
                else:
                    pass_kwargs = {}
            if check["abc"] is True and check["abc_def"] is True:
                return AdminJobResult(Pass=True)
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
            result1 = await self._db_actions(exe, profile)
            print(f"result: {result1}")
        result = AdminJobResult(Pass=True)
        await self.post_process.execute(exe.JobId)
        return self._event(exe, "g2g", result)
