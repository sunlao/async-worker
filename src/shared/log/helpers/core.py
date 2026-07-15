from datetime import UTC
from shared.models.constants import Events, LogLevel
from shared.models.log import Core, Config


def build(config: Config, level: LogLevel, event: Events, msg: str) -> Core:
    """Build Resuable Logging Core"""
    return Core(
        Environment=config.Environment,
        InputLevel=level,
        Time=config.Now(UTC),
        TransactionID=config.UUID4(),
        Event=event,
        Message=f"{config.Service} {msg}",
    )
