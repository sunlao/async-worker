from pytest import fixture
from shared.db import Engine
from shared.log.writer import Writer
from shared.log.helpers.error import Error
from shared.models.constants import UserContext
from shared.models.db import DBStartUpContext
from shared.db.helpers.query import Query


def _query(name: str) -> str:
    return Query().get(name)


@fixture(scope="function", name="startup_ctx")
def f_startup_ctx(config_log) -> Engine:
    return DBStartUpContext(
        UserContext=UserContext.DATA,
        Log=Writer(config_log),
        Config=config_log,
        LogErrorHelper=Error(),
        DBMaxPool=4,
    )


@fixture(scope="function", name="engine")
def f_engine(startup_ctx) -> Engine:
    return Engine(startup_ctx)


@fixture(name="db")
async def f_db(engine):
    db = engine
    await db.startup()
    return db


@fixture(scope="function", name="db_client")
async def f_client(engine: Engine):
    """Create a fresh (or reconnected) DATA pool for each test function."""
    async with engine.client() as conn:
        yield conn


@fixture(scope="function")
def db_execute(
    db_client,
):
    async def _execute(query_name: str, *args) -> None:
        await db_client.execute(_query(query_name), *args)

    return _execute


@fixture(scope="function")
def db_execute_many(db_client):
    async def _db_execute_many(query_name: str, args: list[tuple]):
        await db_client.executemany(_query(query_name), args)

    return _db_execute_many


@fixture(scope="function")
def db_get_one(db_client):
    async def _get_one(query_name: str, *args) -> tuple | None:
        row = await db_client.fetchrow(_query(query_name), *args)
        return None if row is None else tuple(row.values())

    return _get_one


@fixture(scope="function")
def db_get_many(db_client):
    async def _get_many(query_name: str, *args) -> list[tuple]:
        rows = await db_client.fetch(_query(query_name), *args)
        return [tuple(r.values()) for r in rows]

    return _get_many


@fixture(scope="function")
def data_context():
    return UserContext.DATA
