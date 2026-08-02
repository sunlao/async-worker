from taskiq import TaskiqState, TaskiqDepends
from cp.handler.hello import Hello
from shared.models.worker import JobConfig, HelloConfig


class Router:
    """Fan out jobs to handlers for execution and logging by Job Type"""

    def __init__(self, context: TaskiqState = TaskiqDepends()):
        self.context = context

    async def hello(self, config: JobConfig[HelloConfig]) -> None:
        await Hello(self.context).handle(config)
