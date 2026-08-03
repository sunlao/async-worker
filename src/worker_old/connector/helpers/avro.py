from io import BytesIO
from json import dumps
from copy import deepcopy
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Dict, Mapping, Tuple, Sequence, Iterable
from fastavro import writer as avro_writer, parse_schema, reader
from shared.models.worker import SerializeInput, SerializeOutput


class Avro:
    """Help connectors serialize between python tuples and avro"""

    @staticmethod
    def _bytes(normalized_iter: Iterable[dict[str, str]], schema_avro: Any) -> bytes:
        buf = BytesIO()
        avro_writer(buf, schema_avro, normalized_iter, codec="deflate")
        return buf.getvalue()

    def _clean_rows(self, rows, fields: Sequence[str]):
        flds = tuple(fields)
        coerce = self._coerce
        for r in rows:
            yield {k: coerce(r.get(k, "")) for k in flds}

    @staticmethod
    def _coerce(v: object) -> str:
        return "" if v is None else str(v)

    @staticmethod
    def _schema_filter(schema, column):
        columns = [detail["name"] for detail in schema["fields"]]
        not_in = [c for c in column if c not in columns]
        if not_in:
            raise ValueError(f"column_filters not in schema: {not_in}")
        return {
            **schema,
            "fields": [{"name": c, "type": "string"} for c in column],
        }

    @staticmethod
    def _schema_hash(schema: Dict[str, Any]) -> str:
        return sha256(
            dumps(schema, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()[:16]

    def _schema(
        self, dto: SerializeInput, column_filters: Sequence[str] | None = None
    ) -> Dict[str, Any]:
        if dto.Schema is None:
            field_names = sorted({k for r in dto.Rows for k in r.keys()})
            schema = {
                "type": "record",
                "name": dto.Name,
                "namespace": "awork",
                "fields": [{"name": k, "type": "string"} for k in field_names],
            }
        else:
            schema = {
                "type": "record",
                "name": dto.Name,
                "namespace": "awork",
                "fields": dto.Schema,
            }

        if column_filters:
            schema = self._schema_filter(schema, column_filters)
        fields = [f["name"] for f in schema["fields"]]
        return {
            "schema": schema,
            "schema_avro": parse_schema(deepcopy(schema)),
            "fields": fields,
        }

    def serialize(self, dto: SerializeInput, **kwargs) -> SerializeOutput:
        """Serialize tuples to Avro"""
        column_filters = kwargs.get("column_filters", None)
        if column_filters == []:
            column_filters = None

        schema = self._schema(dto, column_filters)
        fields = schema["fields"]
        rows = self._clean_rows(dto.Rows, fields)

        schema_fp = self._schema_hash(schema["schema"])
        schema_fp_bytes = schema_fp.encode("utf-8")

        h = sha256()
        h.update(b"v1|")
        h.update(schema_fp_bytes)
        h.update(b"|")

        row_count = 0

        def _hash_then_yield() -> Iterable[dict[str, str]]:
            nonlocal row_count
            sep = "\x1f".encode("utf-8")
            for r in rows:
                canon = sep.join((r.get(k, "") or "").encode("utf-8") for k in fields)
                h.update(canon)
                row_count += 1
                yield r

        bytes_a = self._bytes(_hash_then_yield(), schema["schema_avro"])
        source_hash = h.hexdigest()

        return SerializeOutput(
            AvroBytes=bytes_a,
            SchemaJSON=schema["schema"],
            SchemaSHA256=schema_fp,
            BytesSHA256=source_hash,
            BytesLen=len(bytes_a),
            RowCount=row_count,
        )

    def deserialize(self, dto: SerializeOutput) -> Tuple[Mapping[str, str], ...]:
        """Deserialize avro to tuples"""
        buf = BytesIO(dto.AvroBytes)
        out: list[Mapping[str, str]] = []
        for rec in reader(buf):
            normalized = {k: ("" if v is None else str(v)) for k, v in rec.items()}
            out.append(MappingProxyType(normalized))
        return tuple(out)
