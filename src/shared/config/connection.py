# edge-allow: pathlib, open, yaml.safe_load
from pathlib import Path
from yaml import safe_load
from shared.models.config import ConnectionInputConfig
from shared.models.worker import ConnectionProfile


class Connection:
    """Read connection-profile declarations during startup."""

    def __init__(self, config: ConnectionInputConfig):
        path = Path(config.ConnectionPath)
        file = f"connection{config.ConnectionVersion}.yml"
        self.yml_path = path.joinpath(file)
        self.profiles = tuple(self._profile(profile) for profile in self._yml())
        if self._check_duplicate() is True:
            raise RuntimeError("Connection profile names must be unique")

    @staticmethod
    def _profile(config: dict) -> ConnectionProfile:
        return ConnectionProfile(
            Name=config["name"],
            ConnectorType=config["connector_type"],
            ResourceType=config.get("resource_type"),
        )

    def _check_duplicate(self) -> bool:
        names = [p.Name for p in self.profiles]
        return len(names) != len(set(names))

    def _yml(self) -> list[dict]:
        with self.yml_path.open("r", encoding="utf-8") as file_obj:
            connection_yml = safe_load(file_obj)
        return connection_yml["profiles"]

    def profile(self, name: str) -> ConnectionProfile | None:
        return next((p for p in self.profiles if p.Name == name), None)
