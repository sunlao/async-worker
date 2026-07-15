from shared.models.api import AdminExecutionResults


class OpsLedger:

    def __init__(self, arq_client, db, uuid):
        self.arq = arq_client
        self.db = db
        self.uuid = uuid

    async def _max_dt(self):
        sql = """select coalesce(max(finish_time), '1970-01-01'::timestamptz)
        max_dt from raw.ops_ledger"""
        async with self.db.client() as conn:
            row = await conn.fetchrow(sql)
        return row["max_dt"]

    @staticmethod
    def _update_sql(col_sql, update_values, updates):
        return f"""
            INSERT INTO raw.ops_ledger ({col_sql})
            VALUES {", ".join(update_values)}
            ON CONFLICT (run_id) DO UPDATE
            SET {updates};
        """  # nosec B608

    @staticmethod
    def _update_values(data_rows, cols):
        param_index = 1
        update_values = []
        params = []
        col_count = len(cols)
        for row in data_rows:
            placeholders = ", ".join(f"${param_index + i}" for i in range(col_count))
            update_values.append(f"({placeholders})")
            params.extend(row[c] for c in cols)
            param_index += col_count
        return update_values, params

    async def load(self) -> AdminExecutionResults:
        rows = await self.arq.ledger(await self._max_dt())
        if rows != set():
            data_rows = [dto.model_dump(by_alias=True) for dto in rows]
            cols = list(data_rows[0].keys())
            col_sql = ", ".join(cols)
            updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in cols if c != "run_id")
            update_values, params = self._update_values(data_rows, cols)
            sql = self._update_sql(col_sql, update_values, updates)
            async with self.db.client() as conn:
                await conn.execute(sql, *params)
        return AdminExecutionResults(
            ExecutionId=self.uuid(), Code=0, Message="Job: OpsLedger complete"
        )
