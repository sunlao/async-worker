from taskiq.abc.broker import AsyncBroker
from cp.unique_job import UniqueJob
from shared.models.config import Redis


class Queue:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.url = f"redis://{self.redis.Host}:{self.redis.Port}"

    def _broker(self) -> AsyncBroker:
        backend = self.redis.Backend(redis_url=self.url, result_ex_time=14400)
        return self.redis.Broker(
            url=self.url, ack_type="when_executed"
        ).with_result_backend(backend)

    def build(self) -> AsyncBroker:
        unique_job = UniqueJob(self.redis.Client.from_url(self.url))
        return self._broker().with_middlewares(unique_job)
