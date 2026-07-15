class Admin:
    admin_activity = """
SELECT
COUNT(*) AS client_conns,
COUNT(*) FILTER (WHERE state = 'active') AS active_conns,
COUNT(*) FILTER (WHERE state = 'idle') AS idle_conns,
COUNT(*) FILTER (WHERE state LIKE 'idle in transaction%') AS idle_in_txn_conns,
COUNT(*) FILTER (WHERE wait_event_type = 'Lock')  AS lock_waiting_conns,
COALESCE(MAX(EXTRACT(EPOCH FROM (now() - query_start)) * 1000)
    FILTER (WHERE state = 'active'), 0)::bigint AS longest_active_ms,
COALESCE(MAX(EXTRACT(EPOCH FROM (now() - state_change)) * 1000)
    FILTER (WHERE state = 'idle'), 0)::bigint AS longest_idle_ms,
COALESCE(MAX(EXTRACT(EPOCH FROM (now() - backend_start)) * 1000)
    ,0)::bigint AS max_backend_age_ms
FROM
pg_stat_activity
WHERE
application_name = :app_name"""

    def get(self, p_name: str) -> str:
        return getattr(self, p_name)
