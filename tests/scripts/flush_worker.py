from asyncio import run
from asyncio import sleep as async_sleep
from arq import create_pool
from shared.config.locker import Locker
from shared.queue.arq_client import ARQClient


async def flush():
    locker = Locker()
    arq = ARQClient(locker.redis(), async_sleep, create_pool)
    await arq.startup()
    await arq.flush()
    await arq.shutdown()


run(flush())
