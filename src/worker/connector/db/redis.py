class Redis:
    """Connector for platform-owned Redis client passed from the edge."""

    def __init__(self, context):
        self.redis = context["redis_client"]

    async def upsert(self, key: str, value: str) -> bool:
        return await self.redis.set(key, value)