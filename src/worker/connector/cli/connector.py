# edge-allow: pathlib, open
from pathlib import Path
from csv import DictReader, QUOTE_MINIMAL
from zipfile import ZipFile
from json import load
from contextlib import suppress
from typing import Any, Dict
from asyncio import wait_for, TimeoutError as ATimeoutError
from worker.connector.helpers.json_parser import JSONParser
from worker.connector.helpers.avro import Avro
from shared.models.worker import (
    MovementConfig,
    SerializeInput,
    SerializeOutput,
)
from shared.models.constants import ActionTypes


class CliSourceError(RuntimeError):
    """Raised when the CLI source connector cannot produce valid rows."""


# pylint: disable=too-many-instance-attributes
class Connector:
    """CLI connector to interface"""

    # pylint: disable=duplicate-code
    def __init__(self, ctx):
        self.ctx = ctx
        cwd_parent = Path(self.ctx["data_dir"])
        self.zip_path = cwd_parent.joinpath("zip")
        self.ready_path = cwd_parent.joinpath("ready")
        self.schema_path = cwd_parent.joinpath("schema")
        self.sp = self.ctx["asubprocess"]
        self.avro = Avro()
        self.json_parser = JSONParser(require_flat_object=True)
        self.sleep = ctx["asleep"]

    async def _cmd(self, command: str, stderr_overide: bool) -> bytes:
        """Execute command and return raw stdout bytes."""
        proc = await self.sp.create_subprocess_shell(
            command, stdout=self.sp.PIPE, stderr=self.sp.PIPE
        )
        try:
            stdout, stderr = await wait_for(proc.communicate(), timeout=600)
        except ATimeoutError as exc:
            with suppress(Exception):
                proc.kill()
                await proc.wait()
            raise CliSourceError(f"timeout after {10}s") from exc

        if stderr and stderr_overide is False:
            raise CliSourceError(
                f"stderr not empty ({len(stderr)}) for command {command}"
            )

        if proc.returncode != 0:
            raise CliSourceError(
                f"Return code ({proc.returncode}) for command {command}"
            )
        return stdout

    async def _cmd_json_lines(self, cmd, **kwargs) -> list[str]:
        """Run command and return ALL non-empty stdout lines as UTF-8 text (JSONL)."""
        stdout = await self._cmd(cmd, False)
        sleep_for = int(kwargs.get("sleep", 0))
        if sleep_for > 0:
            await self.sleep(sleep_for)
        return [ln.decode("utf-8").strip() for ln in stdout.splitlines() if ln.strip()]

    @staticmethod
    def _file_to_lines(path: Path, columns: list[str], rules: Dict[str, Any]):
        with open(path, "r", encoding=rules["encoding"], newline=rules["newline"]) as f:
            kwargs = rules["kwargs"]
            kwargs["quoting"] = QUOTE_MINIMAL
            rdr = DictReader(f, fieldnames=columns, **kwargs)
            yield from rdr

    async def _file_to_avro(
        self, config_job: MovementConfig, **kwargs
    ) -> SerializeOutput:
        name = config_job.Source
        ready = self.ready_path.joinpath(name)
        schema = self._schema(name)
        columns = [detail["name"] for detail in schema["details"]]
        rows = self._file_to_lines(ready, columns, schema["rules"])
        dto = SerializeInput(Name=name, Rows=rows, Schema=schema["details"])
        return self.avro.serialize(dto, **kwargs)

    def _schema(self, name):
        schema_path = self.schema_path.joinpath(Path(name).with_suffix(".json"))
        with schema_path.open("r", encoding="utf-8") as handler:
            return load(handler)

    async def source_data(self, config_job: MovementConfig, **kwargs):
        if config_job.ActionType in (ActionTypes.FSTB, ActionTypes.BINU):
            return await self._file_to_avro(config_job, **kwargs)
        if config_job.ActionType == ActionTypes.CTI:
            json_lines = await self._cmd_json_lines(config_job.Cmd, **kwargs)
            schema = self._schema(config_job.Source)["details"]
            dto = self.json_parser.lines_to_input(json_lines, config_job.Source, schema)
            return self.avro.serialize(dto, **kwargs)
        raise CliSourceError(f"Action type: {config_job.ActionType} not supported")

    def unzip(self, name) -> None:
        path = self.zip_path.joinpath(name)
        with ZipFile(path) as zf:
            zf.extractall(self.ready_path)
