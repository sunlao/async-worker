# src/worker/connector/db/postgres.py

from typing import List, Tuple
from worker_old.connector.helpers.avro import Avro
from shared.models.worker import (
    ActionTypes,
    MovementConfig,
    SerializeOutput,
    MovementJobResult,
)


class Postgres:
    """Posgtres DB Connector for connecting to external systems"""

    def __init__(self, ctx, conn):
        self.ctx = ctx
        self.conn = conn
        self.avro = Avro()
        self.job_id = ctx["job_id"]

    def _avro_to_rows(self, avo_dto: SerializeOutput):
        records = self.avro.deserialize(avo_dto)
        avro_cols: List[str] = [f["name"] for f in avo_dto.SchemaJSON["fields"]]
        hash_bytes = bytes.fromhex(avo_dto.BytesSHA256)
        cols: List[str] = avro_cols + ["sys_source_hash", "sys_job_id"]
        rows: List[Tuple] = [
            tuple(rec.get(c) for c in avro_cols) + (hash_bytes, self.job_id)
            for rec in records
        ]
        return cols, rows

    async def _truncate(self, target: str) -> None:
        sql = f"TRUNCATE TABLE {target}"
        await self.conn.execute(sql)

    async def _copy(
        self, config_job: MovementConfig, avo_dto: SerializeOutput
    ) -> MovementJobResult:
        cols, rows = self._avro_to_rows(avo_dto)
        schema, table = config_job.Target.split(".", 1)

        # do the bulk copy
        await self.conn.copy_records_to_table(
            table_name=table,
            schema_name=schema,
            columns=cols,
            records=rows,
        )
        sql = f"SELECT count(*) as count FROM {schema}.{table}"  # nosec B608
        row_cnt = await self.conn.fetchrow(sql)
        return MovementJobResult(
            RowCount=row_cnt["count"],
            ActionType=config_job.ActionType,
            LastHash=avo_dto.BytesSHA256,
        )

    async def _insert(
        self, config_job: MovementConfig, avo_dto: SerializeOutput
    ) -> MovementJobResult:
        cols, rows = self._avro_to_rows(avo_dto)
        sql = self._sql_insert(config_job, cols)
        if len(rows) == 1:
            await self.conn.execute(sql, *rows[0])
        else:
            # many rows: pass list[tuple] directly
            await self.conn.executemany(sql, rows)
        return MovementJobResult(
            RowCount=len(rows),
            ActionType=config_job.ActionType,
            LastHash=avo_dto.BytesSHA256,
        )

    def _sql_insert(self, config_job: MovementConfig, columns: List[str]) -> str:
        sql_cols = ", ".join(columns)
        placeholders = ", ".join(f"${i}" for i in range(1, len(columns) + 1))
        sql = (
            f"INSERT INTO {config_job.Target} ({sql_cols}) "  # nosec B608
            f"VALUES ({placeholders})"  # This is not at risk for SQL injection
        )
        return sql

    async def target(
        self, config_job: MovementConfig, avo_dto: SerializeOutput
    ) -> MovementJobResult:
        if config_job.ActionType == ActionTypes.CTI:
            await self._truncate(config_job.Target)
            return await self._insert(config_job, avo_dto)
        if config_job.ActionType == ActionTypes.FSTB:
            await self._truncate(config_job.Target)
            return await self._copy(config_job, avo_dto)
        raise ValueError(f"unsupported JobType: {config_job.ActionType}")
