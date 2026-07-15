from asyncio import sleep as async_sleep, subprocess
from pathlib import Path
from pytest_asyncio import fixture
from shared.config.reader import Reader
from shared.log.writer import Writer
from shared.log.helpers.error import Error
from shared.models.config import ReaderConfig


test_data = Path.cwd() / "tests" / "data"


@fixture(scope="function")
async def worker_ctx(config_log, config_worker, engine, arq_client):
    ctx = {}

    job_path = test_data / "config"
    job_version = "_test"
    job_version_bad = "_test_bad"

    reader = Reader(
        ReaderConfig(
            JobPath=str(job_path),
            JobVersion=job_version,
        )
    )
    config_reader_bad = ReaderConfig(
        JobPath=str(job_path),
        JobVersion=job_version_bad,
    )

    ctx["config_log"] = config_log
    log = Writer(config_log)
    ctx["log"] = log
    ctx["log_error_helper"] = Error()
    ctx["data_dir"] = config_worker.DataDir
    ctx["reader"] = reader
    ctx["config_reader_bad"] = config_reader_bad
    ctx["enqueue_gate"] = False
    ctx["asleep"] = async_sleep
    db = engine
    await db.startup()
    ctx["db"] = db

    # ARQ pool
    ctx["arq_client"] = arq_client

    # Edge policy + subprocess handle
    ctx["asubprocess"] = subprocess

    try:
        yield ctx
    finally:
        # Teardown in reverse order
        await db.shutdown()
