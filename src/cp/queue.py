from redis.asyncio import Redis
from taskiq import AsyncBroker

from cp.unique_job import UniqueJob
from shared.models.config import Redis as RedisConfig
from shared.models.worker import WorkerInit


class Queue:
    def __init__(self, worker: WorkerInit, config: RedisConfig) -> None:
        self.worker = worker
        self.config = config

    def _broker(self) -> AsyncBroker:
        backend = self.worker.Backend(
            redis_url=self.worker.RedisURL,
            result_ex_time=self.config.ResultExpirationSec,
        )
        return self.worker.Broker(
            url=self.worker.RedisURL, ack_type=self.config.AckType
        ).with_result_backend(backend)

    def build(self) -> AsyncBroker:
        return self._broker().with_middlewares(UniqueJob(self.worker))