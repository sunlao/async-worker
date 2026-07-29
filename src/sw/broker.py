from redis.asyncio import Redis
from taskiq.message import BrokerMessage
from taskiq_redis import RedisStreamBroker

ENQUEUE_SCRIPT = """
if redis.call("SET", KEYS[1], ARGV[1], "NX") == false then
    return false
end

return redis.call("XADD", KEYS[2], "*", "data", ARGV[2])
"""


class UniqueRedisStreamBroker(RedisStreamBroker):
    async def kick(self, message: BrokerMessage) -> None:
        job_id = message.labels.get("job_id")

        if job_id is None:
            await super().kick(message)
            return

        queue_name = message.labels.get("queue_name") or self.queue_name
        active_key = f"taskiq:active:{job_id}"

        async with Redis(connection_pool=self.connection_pool) as redis:
            stream_id = await redis.eval(
                ENQUEUE_SCRIPT,
                2,
                active_key,
                queue_name,
                message.task_id,
                message.message,
            )

        if stream_id is None:
            raise RuntimeError(f"job already active: {job_id}")