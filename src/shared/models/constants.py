from enum import StrEnum
from typing import NamedTuple


class AckTypes(StrEnum):
    WHEN_RECEIVED = "when_received"
    WHEN_EXECUTED = "when_executed"
    WHEN_SAVED = "when_saved"


class ActionTypes(StrEnum):
    """Job Constants for Action Types"""

    NA = "n/a"  # No Action needed (because Same as Source)
    CTI = "C-TI"  # command + Truncate & Insert
    BINU = "binu"  # Binary movement (i.e. uncompressed files)
    BINC = "binc"  # Binary movement (i.e. compressed files)
    FSTB = "FS-TB"  # File With Schema - Truncate & Bulk Load (PG-Copy)
    CDC = "CDC"  # Change Data Capture
    EXE = "execute"  # execute admin job


class ArqStatus(StrEnum):
    """Arq Constants for Status to support API service with interpeting
    worker run results"""

    COMPLETE = "complete"
    FINISHED = "finished"
    SUCCESS = "success"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    DEFERRED = "deferred"
    NOT_FOUND = "not_found"
    UNKNOWN = "unknown"
    QUEUED = "queued"
    INPROGRESS = "in_progress"


class Audit(NamedTuple):
    last_hash: str | None


class DBPoolOutcome(StrEnum):
    """Constants for DB logging types outcomes"""

    REUSE = "reuse_connection"
    RETRY = "retry_connection"
    NEW = "new_connection"
    FAIL = "fail_connection"


class DBUser(StrEnum):
    """Constants for allowed DB users"""

    APP = "awork_app"
    DATA = "awork_data"


class DebugStatus(StrEnum):
    OK = "ok"
    ERROR = "error"


class Environments(StrEnum):
    """Constants for Supported Environments"""

    DEV = "dev"
    CI = "ci"


class Events(StrEnum):
    """Supported Events"""

    STARTUP = "startup"
    SHUTDOWN = "shutdown"
    ACCESS = "access"
    HTTP_ERROR = "http_error"
    DBOPEN = "db_open"
    POOLSNAPSHOT = "pool_snap_shot"
    JOB = "job"
    QUIESCE = "quiesce"


class JobTypes(StrEnum):
    HELLO = "hello"
    ADMIN = "admin"


# Starlette/Uvicorn insist on lower case
class LogLevel(StrEnum):
    """Log Levels formatted for Starlette/Uvicorn"""

    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"


# Starlette/Uvicorn insist on lower case
class PathParts(StrEnum):
    """DTO to Support Tracing Errors. Trace Event paths are filtered and trimmed by
    path parts"""

    SRC = "src"
    TESTS = "tests"


class Services(StrEnum):
    """Async Services"""

    API = "awork-api"
    WORKER = "awork-worker"
    DB = "awork-postgres"
    TEST = "awork-test"
    QUIESCE = "awork-quiesce"


class ConnectorTypes(StrEnum):
    """Connectors for"""

    RDBMS = "rdbms"
    API = "api"
    IO = "io"


class SourceTypes(StrEnum):
    """Connectors for dealing with source systems external to worker"""

    CLI = "cli"
    API = "api"
    ARQ = "arq"


class Tags(StrEnum):
    NATAL = "natal"
    TEST = "test"


class TargetTypes(StrEnum):
    """Connectors for dealing with target systems external to worker"""

    PG = "pg"
    CLI = "cli"
    NA = "na"


class TouchStatuses(StrEnum):
    EXIST = "exist"
    NEW = "new"


class UserContext(StrEnum):
    """ENUM for AsyncServ Profiles"""

    APP = "APP"
    DATA = "DATA"


class ProfileAction(StrEnum):
    """ENUM for Profile create Actions"""

    UPDATE = "UPDATE"
    INSERT = "INSERT"
    DELETE = "DELETE"
