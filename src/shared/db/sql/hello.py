class Hello:
    hello_audit = "select * from raw.audit_dtl($1)"
    hello_count = "select count(*) from awork.hello_world"
    hello_db = "select 'hello' world, 'test' data"
    hello_delete_job = "delete from raw.hello_job where job_id = $1"
    hello_insert = "INSERT INTO awork.hello_world(col1, col2) VALUES ($1, $2)"
    hello_get_job = "SELECT count(*) FROM raw.hello_job"
    hello_test_controller = "SELECT count(*) FROM raw.hello_test_controller"
    hello_test_api_cnt = "SELECT count(*) FROM raw.hello_test_api"
    hello_test_trunc = "truncate table raw.hello_test_api"
    hello_test_api_fail = "SELECT count(*) FROM raw.hello_test_api_fail"

    hello_insert_job = """
WITH ins AS (
    INSERT INTO raw.hello_job (job_id, execution_time)
    VALUES ($1, $2)
    RETURNING job_id, execution_time
)
SELECT count(*) COUNT FROM ins;
    """

    hello_seed_exists = """
select count(*)
from pg_catalog.pg_tables
where schemaname = 'raw'
and tablename  = 'hello_seed'
"""

    hello_seed_drop = "drop table raw.hello_seed"

    hello_job_cnt = "select count(*) from raw.hello_job"

    hello_postgres = "select 'hello_postgres'"

    hello_select = "select * from awork.hello_world where col1 = $1"

    hello_select_many = "select * from awork.hello_world order by col1"

    hello_single_job = """
select job_id from raw.hello_job where job_id not like 'cron:%' limit 1
"""

    hello_truncate = "truncate table awork.hello_world"

    hello_update = """
update awork.hello_world
set
col2 = $2
where
col1 = $1
"""

    def get(self, p_name: str) -> str:
        return getattr(self, p_name)
