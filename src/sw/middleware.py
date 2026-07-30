from typing import Any
from redis.asyncio import Redis
from taskiq import TaskiqMessage, TaskiqMiddleware, TaskiqResult

DELETE_SCRIPT = """
if redis.call("GET", KEYS[1]) == ARGV[1] then
    return redis.call("DEL", KEYS[1])
end

return 0
"""


class ActiveJobMiddleware(TaskiqMiddleware):
    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def post_execute(
        self, message: TaskiqMessage, result: TaskiqResult[Any]
    ) -> None:
        job_id = message.labels.get("job_id")

        if job_id is not None:
            await self.redis.eval(
                DELETE_SCRIPT,
                1,
                f"taskiq:active:{job_id}",
                message.task_id,
            )
