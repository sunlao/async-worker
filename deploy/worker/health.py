import asyncio
from os import environ
from datetime import UTC, datetime
from redis.asyncio import Redis


async def main() -> None:
    redis = Redis(
        host=environ["REDIS_HOST"],port=environ["REDIS_PORT"], decode_responses=True
    )
    try:
        value = await redis.get("awork-worker-heartbeat")
        healthy = (
            value is not None
            and (datetime.now(UTC) - datetime.fromisoformat(value)).total_seconds()
            <= 120
        )
    finally:
        await redis.aclose()
    if not healthy:
        raise SystemExit(1)
if __name__ == "__main__":
    asyncio.run(main())