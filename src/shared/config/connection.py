# edge-allow: pathlib, open, yaml.safe_load
from pathlib import Path
from yaml import safe_load
from shared.models.constants import ConnectionTypes
from shared.models.config import ReaderConfig
from shared.models.worker import AdminConfig, ConnectionConfig, HelloConfig


class Connnection:
    """Utility to read Connection yml during connector"""

    def __init__(self, config: ReaderConfig):
        connection_path = Path(config.ConnectionPath)
        file = f"connection{config.ConnectionVersion}.yml"
        self.yml_path = connection_path.joinpath(file)
        self.configs = [self._connection_config(c, c["connection_type"]) for c in self._yml()]
        results = self._validate()
        if len(results) != 0:
            raise RuntimeError(f"Config is not valid for {str(results)}")

    def _check_item(self, items: list) -> bool:
        return len(items) == len(set(items))

    def _check_obj(self, obj: dict[str, list]) -> dict[str, bool]:
        return {k: self._check_item(v) for k, v in obj.items()}

    def _connection_config(self, config, connection_type: ConnectionTypes) -> ConnectionConfig:
        if connection_type == ConnectionTypes.ADMIN:
            dto: ConnectionConfig[AdminConfig] = ConnectionConfig(
                Type=connection_type,
                Id=config["id"],
                Config=self._admin(config),
                KWARGS=tuple(config.get("kwargs", {}).items()),
            )
            return dto
        if connection_type == ConnectionTypes.HELLO:
            dto: ConnectionConfig[HelloConfig] = ConnectionConfig(
                Type=connection_type,
                Id=config["id"],
                Config=self._hello(config),
                KWARGS=tuple(config.get("kwargs", {}).items()),
            )
            return dto
        raise RuntimeError(f"ConnectionType: {connection_type} is not Supported")

    def _hello(self, config) -> HelloConfig:
        return HelloConfig(
            Name=config["name"],
            ActionType=config["action_type"],
            ConnectionProfile=config["connection_profile"],
            Cmd=config["cmd"],
            **self._optional(config),
        )

    @staticmethod
    def _optional(config) -> dict:
        keymap = {
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
            connection_yml = safe_load(file_obj)
        return connection_yml["connections"]

    def config(self, connection_id: int) -> ConnectionConfig | None:
        return next(filter(lambda c: c.Id == connection_id, self.configs), None)

    def startup_configs(self, connection_type: ConnectionTypes) -> tuple[ConnectionConfig, ...]:
        return tuple(
            c for c in self.configs if c.Type == connection_type and c.Config.StartUp is True
        )
