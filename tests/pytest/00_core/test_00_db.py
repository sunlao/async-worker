async def test_hello_postgres_app(db_get_one):
    await db_get_one("hello_postgres")


async def test_hello_postgres_data(db_get_one):
    assert await db_get_one("hello_postgres")


async def test_hello_truncate(db_execute, db_get_one):
    await db_execute("hello_truncate")
    row = await db_get_one("hello_count")
    assert row[0] == 0


async def test_hello_insert_one(db_execute, db_get_one):
    args = ("abc", 123)
    await db_execute("hello_insert", *args)
    row = await db_get_one("hello_count")
    assert row[0] == 1


async def test_hello_insert_many(db_execute_many, db_get_one):
    args = [("def", 456), ("ghi", 789)]
    await db_execute_many("hello_insert", args)
    row = await db_get_one("hello_count")
    assert row[0] == 3


async def test_hello_select(db_get_one):
    args = "abc"
    row = await db_get_one("hello_select", args)
    assert row == ("abc", 123)


async def test_hello_select_many(db_get_many):
    result = await db_get_many("hello_select_many")
    assert result == [("abc", 123), ("def", 456), ("ghi", 789)]


async def test_hello_update(db_execute, db_get_one):
    args1 = ("abc", -99)
    await db_execute("hello_update", *args1)
    args2 = "abc"
    row = await db_get_one("hello_select", args2)
    assert row == ("abc", -99)
