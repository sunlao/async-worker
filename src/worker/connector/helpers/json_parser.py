from typing import Mapping
from json import loads as json_loads, JSONDecodeError
from shared.models.worker import SerializeInput


class JSONStrError(RuntimeError):
    """Raised when a JSON line is invalid or the shape is unsupported."""


class JSONParser:
    def __init__(self, require_flat_object: bool = False):
        self.require_flat_object = require_flat_object

    @staticmethod
    def _is_flat(obj: Mapping) -> bool:
        return all(not isinstance(v, (dict, list, tuple)) for v in obj.values())

    def _decode_jsonl(self, lines: list[str]) -> list[dict]:
        rows: list[dict] = []
        for s in lines:
            try:
                obj = json_loads(s)
            except JSONDecodeError as exc:
                raise JSONStrError("invalid JSON line") from exc
            if not isinstance(obj, dict):
                raise JSONStrError("JSONL line must be a JSON object")
            if self.require_flat_object and not self._is_flat(obj):
                raise JSONStrError("row objects must be flat (no nested structures)")
            rows.append(obj)
        return rows

    def lines_to_input(
        self, json_lines: list[str], name: str, schema
    ) -> SerializeInput:
        rows = self._decode_jsonl(json_lines)
        return SerializeInput(Name=name, Rows=tuple(rows), Schema=schema)
