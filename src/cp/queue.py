from taskiq.abc.broker import AsyncBroker
from shared.models.config import Redis


class Queue:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.url = f"redis://{self.redis.Host}:{self.redis.Port}"

    def _broker(self):
        backend = self.redis.Backend(redis_url=self.url, result_ex_time=14400)
        return self.redis.Broker(
            url=self.url, ack_type="when_executed"
        ).with_result_backend(backend)

    def build(self) -> AsyncBroker:
        self.middleware = self.redis.Middleware(
            default_retry_label=False, default_delay=60
        )
        broker = self._broker()
        return broker.with_middlewares(self.middleware)