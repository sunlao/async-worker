from asyncio import sleep
from pytest import fixture
from arq import create_pool
from shared.queue.arq_client import ARQClient


@fixture
async def arq_client(redis_config):
    arq = ARQClient(redis_config, sleep, create_pool)
    await arq.startup()
    try:
        yield arq
    finally:
        await arq.shutdown()
