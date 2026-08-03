from enum import StrEnum
from typing import NamedTuple


class AckTypes(StrEnum):
    WHEN_RECEIVED = "when_received"
    WHEN_EXECUTED = "when_executed"
    WHEN_SAVED = "when_saved"


class ActionTypes(StrEnum):
    """Job Constants for Action Types
    - clients
    """

    SELECT_ONE = "select_one"  # select one w/ optional args in the KWARG
    SELECT_MANY = "select_many"  # select many w/ optional args in the KWARG
    EXECUTE_ONE = "execute_one"  # exeucte one w/ optional args in the KWARG
    EXECUTE_MANY = "execute_many"  # execute many w/ optional args in the KWARG
    SUBPROCESS = "SUBPROCESS"  # issue subprocces command
    GET = "get"  # GET response from API
    POST = "post"


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


class ConnectorTypes(StrEnum):
    """Connectors for"""

    DB = "db"
    API = "api"
    IO = "io"


class Tags(StrEnum):
    NATAL = "natal"
    TEST = "test"


class Targets(StrEnum):
    """Worker Target Names
    - unity service pod components
    - unity centrally managed components
    - external component names (tbd)
    """

    UNITY_WORKER_DB = "unity_worker_db"
    UNITY_WORKER_API = "unity_worker_api"
    UNITY_WORKER_IO = "unity_worker_io"
    UNITY_QUIESCE_API = "unity_quiesce_api"


class TouchStatuses(StrEnum):
    EXIST = "exist"
    NEW = "new"


class UserContext(StrEnum):
    """ENUM for AsyncServ Profiles"""

    APP = "APP"
    DATA = "DATA"
