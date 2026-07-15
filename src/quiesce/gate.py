from pathlib import Path
from shared.models.api import AdminExecutionResults


class Gate:

    def __init__(self, config, uuid):
        self.path = Path(config.GatePath)
        self.uuid = uuid

    def close(self) -> bool:
        self.path.touch(exist_ok=True)
        return AdminExecutionResults(
            ExecutionId=self.uuid(), Code=0, Message="Close Gate"
        )

    def open(self) -> None:
        self.path.unlink(missing_ok=True)
        return AdminExecutionResults(
            ExecutionId=self.uuid(), Code=0, Message="Open Gate"
        )
