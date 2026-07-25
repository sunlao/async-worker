from os import getenv
from os.path import join
from datetime import datetime
from time import perf_counter
from uuid import uuid4
from urllib.parse import quote
from shared.models.api import aworkConfig
from shared.models.constants import DBUser, UserContext
from shared.models.config import DBSecrets, Quiesce, Redis
from shared.models.log import Config
from shared.models.worker import WorkerConfig


class NoValidEnvironment(Exception):
    """Raised when an unsupported ENV system variable is set."""

    def __init__(self, env: str, message: str = "Only dev and ci are supported"):
        super().__init__(f"System ENV variable: {env}. {message}")


class Locker:
    """Configs and Secrets managed at the Edge"""

    def __init__(self):
        self.true_values = ("1", "true", "yes", "on", 1)
        self.env = getenv("ENV", "false")

    def awork(self):
        return aworkConfig(
            JobPath=getenv("JOB_PATH"),
            JobVersion=getenv("JOB_VERSION"),
            AppVersion=self._app_version(),
            DBMaxPool=int(getenv("DB_MAX_POOL")),
            GatePath=getenv("GATE_CLOSE_PATH", "dev"),
        )

    @staticmethod
    def _app_version():
        path = "/app/VERSION"
        with open(path, encoding="UTF-8") as file_obj:
            version = file_obj.read()
        return version

    def db(self, user_context: UserContext) -> DBSecrets:
        """Get DB secrets with config. Only supports retrieval from environment
        Variables"""
        app_code = getenv("APP_CODE")
        if self.env in {"dev", "ci"}:
            return DBSecrets(
                HOST=f"{app_code}-postgres",
                USER=getattr(DBUser, user_context),
                PASSWORD=quote(getenv(f"DB_{user_context}_PWD")),
                DB_NAME=f"db_{app_code}",
                PORT=int(getenv("DB_PORT")),
                SERVICE=getenv("SERVICE"),
            )
        raise NoValidEnvironment(self.env)

    def worker(self):
        start_up = getenv("START_UP", "true").strip().lower() in self.true_values
        return WorkerConfig(
            StartUp=start_up,
            JobPath=getenv("JOB_PATH"),
            JobVersion=getenv("JOB_VERSION"),
            DBMaxPool=int(getenv("DB_MAX_POOL")),
            DataDir=getenv("DATA_DIR"),
            GatePath=getenv("GATE_CLOSE_PATH", "dev"),
            Retry=getenv("WORKER_RETRY"),
        )

    def log(self) -> Config:
        """Log Config"""
        log_to_file = getenv("LOG_TO_FILE", "true").strip().lower() in self.true_values
        if self.env in {"dev", "ci"}:
            return Config(
                Level=getenv("LOG_LEVEL"),
                Service=getenv("SERVICE"),
                LogToFile=log_to_file,
                LogDirectory=join(getenv("LOG_DIR"), f"{getenv('SERVICE')}.log"),
                BackUpCount=int(getenv("BACKUP_COUNT", "10")),
                Environment=self.env,
                Now=datetime.now,
                TimeCounter=perf_counter,
                UUID4=uuid4,
            )
        raise NoValidEnvironment(self.env)

    @staticmethod
    def redis() -> Redis:
        """Redis Config"""
        return Redis(
            Host=getenv("REDIS_HOST", "localhost"),
            Port=int(getenv("REDIS_PORT", "6379")),
            RedisPingAttempts=int(getenv("REDIS_PING_ATTEMPTS", "5")),
            RedisPingDelaySec=float(getenv("REDIS_PING_DELAY_SEC", "0.5")),
            Environment=getenv("ENV", "dev"),
            AppCode=getenv("APP_CODE", "awork"),
            WaitFor=int(getenv("WaitFor", "2")),
        )

    @staticmethod
    def quiesce() -> Quiesce:
        return Quiesce(
            GatePath=getenv("GATE_CLOSE_PATH", "dev"),
            TimeOut=1800,
            DBMaxPool=int(getenv("DB_MAX_POOL")),
        )
