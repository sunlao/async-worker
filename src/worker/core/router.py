from taskiq import AsyncBroker, TaskiqDepends, TaskiqState
from shared.models.constants import JobTypes
from shared.models.worker import HelloConfig, JobConfig
from worker.handler.hello import Hello


async def hello(
    config: JobConfig[HelloConfig], context: TaskiqState = TaskiqDepends(),
) -> None:
    """Route a dequeued Hello job to its handler."""
    await Hello(context).handle(config)


def register(queue: AsyncBroker) -> AsyncBroker:
    """Register job-type routes with the Taskiq queue."""
    queue.task(task_name=JobTypes.HELLO)(hello)
    return queue