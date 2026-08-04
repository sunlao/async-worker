from asyncpg import connect
from shared.config.locker import Locker
from shared.models.db import DBConnInput, DBConnection


async def connection(dto: DBConnInput) -> DBConnection:
    """Open Function for database.  Redundant db prefix to avoid shadow py sl open"""
    s = Locker().db(dto.UserContext)
    dsn = f"postgresql://{s.USER.lower()}:{s.PASSWORD}@{s.HOST}:{s.PORT}/{s.DB_NAME}"
    db_app_name = f"{s.SERVICE}-{dto.UserContext}".lower()
    conn = await connect(dsn, server_settings={"application_name": db_app_name})
    conn_ms = int((dto.Config.TimeCounter() - dto.StartElapsed) * 1000)
    return DBConnection(
        Connection=conn,
        Elapsed_ms=conn_ms,
    )


async def target_exists(db, target: str) -> None:
    sql = "select count(to_regclass($1)) as check"
    async with db.client() as conn:
        row = await conn.fetchrow(sql, target)
    if row["check"] != 1:
        raise RuntimeError(f"DB target: {target} must Exist")
