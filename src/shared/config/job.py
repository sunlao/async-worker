# edge-allow: pathlib, open, yaml.safe_load
from pathlib import Path
from yaml import safe_load
from shared.models.constants import JobTypes
from shared.models.config import JobInputConfig
from shared.models.worker import AdminConfig, JobConfig, HelloConfig, Query


class Job:
    """Utility to Read Job yml during queue Startup"""

    def __init__(self, config: JobInputConfig):
        job_path = Path(config.JobPath)
        file = f"job{config.JobVersion}.yml"
        self.yml_path = job_path.joinpath(file)
        self.configs = [self._job_config(c, c["job_type"]) for c in self._yml()]
        results = self._validate()
        if len(results) != 0:
            raise RuntimeError(f"Config is not valid for {str(results)}")

    def _admin(self, config) -> AdminConfig:
        return AdminConfig(
            Name=config["name"],
            SourceConnectionProfile=config["source_connection_profile"],
            SourceCmd=config.get("source_cmd", ""),
            TargetConnectionProfile=config.get("target_connection_profile", ""),
            TargetCmd=config.get("target_cmd", ""),
            **self._optional(config),
        )

    def _check_item(self, items: list) -> bool:
        return len(items) == len(set(items))

    def _check_obj(self, obj: dict[str, list]) -> dict[str, bool]:
        return {k: self._check_item(v) for k, v in obj.items()}

    def _job_config(self, config, job_type: JobTypes) -> JobConfig:
        if job_type == JobTypes.ADMIN:
            dto: JobConfig[AdminConfig] = JobConfig(
                Type=job_type,
                Id=config["id"],
                Config=self._admin(config),
                KWARGS=tuple(config.get("kwargs", {}).items()),
            )
            return dto
        if job_type == JobTypes.HELLO:
            dto: JobConfig[HelloConfig] = JobConfig(
                Type=job_type,
                Id=config["id"],
                Config=self._hello(config),
                KWARGS=tuple(config.get("kwargs", {}).items()),
            )
            return dto
        raise RuntimeError(f"JobType: {job_type} is not Supported")

    def _hello(self, config) -> HelloConfig:
        query = tuple(
            Query(
                Name=query["name"],
                ActionType=query["action_type"],
                PassResultFlag=bool(query.get("pass_result_flag", False)),
                Args=tuple(tuple(arg) for arg in (query.get("args") or ())),
            )
            for query in config.get("queries", ())
        )
        return HelloConfig(
            Name=config["name"],
            ConnectionProfile=config["connection_profile"],
            Queries=query,
            **self._optional(config),
        )

    @staticmethod
    def _optional(config) -> dict:
        keymap = {
            "cmd": "Cmd",
            "action_type": "ActionType",
            "startup": "StartUp",
            "delay": "Delay",
            "run_once": "RunOnce",
            "run_next": "RunNext",
            "retry": "Retry",
        }
        return {v: config[k] for k, v in keymap.items() if k in config}

    def _validate(self):
        """Return a Validation key with a False value if check failed for:
        - id's must be unique
        - names must be unique
        - source target combinations must be unique
        - every id in a RunNext list must exist as an id
        """
        ids = [c.Id for c in self.configs]
        names = [c.Config.Name for c in self.configs]
        run_nexts = [c.Config.RunNext for c in self.configs if c.Config.RunNext]
        next_ids = [i for r in run_nexts for i in r]
        tests = [{"Ids": ids}, {"Names": names}]
        results = [self._check_obj(t) for t in tests]
        results.append({"next": False for i in next_ids if i not in ids})
        return [k for r in results for k, v in r.items() if v is False]

    def _yml(self):
        with self.yml_path.open("r", encoding="utf-8") as file_obj:
            job_yml = safe_load(file_obj)
        return job_yml["jobs"]

    def config(self, job_id: int) -> JobConfig | None:
        return next(filter(lambda c: c.Id == job_id, self.configs), None)

    def startup_configs(self, job_type: JobTypes) -> tuple[JobConfig, ...]:
        return tuple(
            c for c in self.configs if c.Type == job_type and c.Config.StartUp is True
        )
