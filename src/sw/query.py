import asyncio
import os

from redis.asyncio import Redis


STREAM = "taskiq"
GROUP = "taskiq"


async def main() -> None:
    redis = Redis(
        host=os.environ["REDIS_HOST"],
        port=int(os.environ["REDIS_PORT"]),
        decode_responses=True,
    )

    groups = await redis.xinfo_groups(STREAM)
    print("groups:", groups)

    pending = await redis.xpending_range(
        STREAM,
        GROUP,
        min="-",
        max="+",
        count=100,
    )
    print("pending:", pending)

    # entries = await redis.xrange(STREAM, min="-", max="+")
    # print("entries:", entries)

    await redis.aclose()


if __name__ == "__main__":
    asyncio.run(main())
