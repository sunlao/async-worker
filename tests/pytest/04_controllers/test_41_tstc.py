from asyncio import timeout, sleep
from pathlib import Path
from worker.connector.cli.connector import Connector as cli


async def test_cli_connector(worker_ctx, tstc_pg_job, tstc_pg_kwarg):
    line_count = 0
    async with timeout(300):
        while line_count == 0:
            try:
                s_output = await cli(worker_ctx).source_data(
                    tstc_pg_job, **tstc_pg_kwarg
                )
                path = Path("/data", "ready", "cities1000.txt")
                with open(path, "rb") as f:
                    line_count = sum(1 for _ in f)
                assert line_count == s_output.RowCount
                assert tstc_pg_kwarg["column_filters"] == [
                    f["name"] for f in s_output.SchemaJSON["fields"]
                ]
            except FileNotFoundError:
                await sleep(30)
            except Exception:  # pylint: disable=broad-exception-caught
                await sleep(10)
