from taskiq import AsyncBroker
from worker.core.extensions.acknowledge import Acknowledge
from worker.core.extensions.enqueue import Enqueue
from shared.models.config import Redis as RedisConfig
from shared.models.worker import WorkerInitContext


class Queue:
    """Create queue with frameworkd's broker
    - set up backend with redis
    - configure
    - add Unique job middle ware
    """

    def __init__(self, worker: WorkerInitContext, config: RedisConfig) -> None:
        self.context = worker
        self.config = config

    def _broker(self) -> AsyncBroker:
        backend = self.context.Backend(
            redis_url=self.context.RedisURL,
            result_ex_time=self.config.ResultExpirationSec,
        )
        return self.context.Broker(
            url=self.context.RedisURL, consumer_id="0"
        ).with_result_backend(backend)

    def build(self) -> AsyncBroker:
        return self._broker().with_middlewares(
            Acknowledge(self.context.RedisClient), Enqueue(self.context.RedisClient)
        )
