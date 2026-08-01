from taskiq import TaskiqState, TaskiqDepends
from cp.handler.hello import Hello
from shared.models.worker import JobConfig, HelloConfig


class Router:
    """Fan out jobs to handlers for execution and logging by Job Type"""
    
    async def hello(
        self, config: JobConfig[HelloConfig], context: TaskiqState = TaskiqDepends()
    ) -> None:
        await Hello(context).handle(config)
