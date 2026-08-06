-- TABLES
CREATE TABLE IF NOT EXISTS awork.hello_world (
	col1 text null,
	col2 int4 null
);

CREATE TABLE IF NOT EXISTS awork.hello_job (
	col1 text null,
	col2 text null
);


CREATE TABLE IF NOT EXISTS  support.ops_ledger (
    job_type        text NOT NULL,
    job_id          int NOT NULL,
    job_name        text NOT NULL,
    action_type     text NOT NULL,
    source          text,
    source_type     text,
    job_target      text,
    target_type     text,
    cmd             text,
    startup         bool NOT NULL,
    run_once        bool NOT NULL,
    run_next        text,
    job_try         int NOT NULL,
    run_id          text NOT NULL,
    enqueue_time    timestamptz NOT NULL,
    start_time      timestamptz NOT NULL,
    finish_time     timestamptz NOT NULL,  
    job_status      bool NOT NULL,
    job_message     text NOT NULL,
    CONSTRAINT house_uk1 UNIQUE (run_id)
);


