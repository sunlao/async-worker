from taskiq import AsyncBroker
from cp.unique_job import UniqueJob
from shared.models.config import Redis
from shared.models.worker import WorkerInit


class Queue:
    def __init__(self, worker: WorkerInit, config: Redis):
        self.worker = worker
        self.url = f"redis://{config.redis.Host}:{config.redis.Port}"

    def _broker(self) -> AsyncBroker:
        backend = self.worker.Backend(redis_url=self.url, result_ex_time=14400)
        return self.worker.Broker(
            url=self.url, ack_type="when_executed"
        ).with_result_backend(backend)

    def build(self) -> AsyncBroker:
        unique_job = UniqueJob(self.worker.RedisClient.from_url(self.url))
        return self._broker().with_middlewares(unique_job)
