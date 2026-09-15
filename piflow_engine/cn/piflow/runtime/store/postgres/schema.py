from __future__ import annotations


PIFLOW_RUN_TRACKING_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS piflow_flow_run (
    id BIGSERIAL PRIMARY KEY,
    process_id VARCHAR(128) NOT NULL UNIQUE,
    flow_uuid VARCHAR(128),
    flow_name VARCHAR(255) NOT NULL,
    status VARCHAR(32) NOT NULL,
    progress NUMERIC(5, 4) NOT NULL DEFAULT 0,
    total_stop_count INTEGER NOT NULL DEFAULT 0,
    success_stop_count INTEGER NOT NULL DEFAULT 0,
    failed_stop_count INTEGER NOT NULL DEFAULT 0,
    skipped_stop_count INTEGER NOT NULL DEFAULT 0,
    workspace_path TEXT,
    log_path TEXT,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS piflow_stop_job_run (
    id BIGSERIAL PRIMARY KEY,
    flow_run_id BIGINT NOT NULL REFERENCES piflow_flow_run(id) ON DELETE CASCADE,
    job_id VARCHAR(128) NOT NULL,
    stop_name VARCHAR(255) NOT NULL,
    stop_uuid VARCHAR(128),
    bundle TEXT,
    status VARCHAR(32) NOT NULL,
    input_ports JSONB NOT NULL DEFAULT '[]',
    output_ports JSONB NOT NULL DEFAULT '[]',
    workspace_path TEXT,
    log_path TEXT,
    stdout_log_path TEXT,
    stderr_log_path TEXT,
    final_output_path TEXT,
    stop_workspace_path TEXT,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(flow_run_id, job_id)
);

CREATE TABLE IF NOT EXISTS piflow_batch_run (
    id BIGSERIAL PRIMARY KEY,
    batch_id VARCHAR(128) NOT NULL UNIQUE,
    user_id VARCHAR(128) NOT NULL,
    dag_task_id VARCHAR(128) NOT NULL,
    definition_id VARCHAR(128) NOT NULL,
    input_dir TEXT NOT NULL,
    output_dir TEXT NOT NULL,
    status VARCHAR(32) NOT NULL,
    max_parallel INTEGER NOT NULL DEFAULT 5,
    retry_count INTEGER NOT NULL DEFAULT 1,
    stop_on_failure BOOLEAN NOT NULL DEFAULT FALSE,
    total_count INTEGER NOT NULL DEFAULT 0,
    submitted_count INTEGER NOT NULL DEFAULT 0,
    completed_count INTEGER NOT NULL DEFAULT 0,
    failed_count INTEGER NOT NULL DEFAULT 0,
    skipped_count INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS piflow_batch_item_run (
    id BIGSERIAL PRIMARY KEY,
    batch_run_id BIGINT NOT NULL REFERENCES piflow_batch_run(id) ON DELETE CASCADE,
    item_index INTEGER NOT NULL,
    input_name VARCHAR(512) NOT NULL,
    input_path TEXT NOT NULL,
    output_path TEXT NOT NULL,
    process_id VARCHAR(128),
    status VARCHAR(32) NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(batch_run_id, item_index)
);

ALTER TABLE piflow_flow_run
ADD COLUMN IF NOT EXISTS log_path TEXT;

ALTER TABLE piflow_stop_job_run
ADD COLUMN IF NOT EXISTS log_path TEXT;

ALTER TABLE piflow_stop_job_run
ADD COLUMN IF NOT EXISTS stdout_log_path TEXT;

ALTER TABLE piflow_stop_job_run
ADD COLUMN IF NOT EXISTS stderr_log_path TEXT;

ALTER TABLE piflow_stop_job_run
ADD COLUMN IF NOT EXISTS final_output_path TEXT;

CREATE INDEX IF NOT EXISTS idx_piflow_flow_run_status
ON piflow_flow_run(status);

CREATE INDEX IF NOT EXISTS idx_piflow_flow_run_created_at
ON piflow_flow_run(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_piflow_stop_job_run_flow_run_id
ON piflow_stop_job_run(flow_run_id);

CREATE INDEX IF NOT EXISTS idx_piflow_stop_job_run_status
ON piflow_stop_job_run(status);

CREATE INDEX IF NOT EXISTS idx_piflow_stop_job_run_stop_name
ON piflow_stop_job_run(stop_name);

CREATE INDEX IF NOT EXISTS idx_piflow_batch_run_user_created
ON piflow_batch_run(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_piflow_batch_run_definition
ON piflow_batch_run(definition_id);

CREATE INDEX IF NOT EXISTS idx_piflow_batch_item_run_batch
ON piflow_batch_item_run(batch_run_id, item_index);

CREATE INDEX IF NOT EXISTS idx_piflow_batch_item_run_status
ON piflow_batch_item_run(status);

CREATE OR REPLACE FUNCTION piflow_touch_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_piflow_flow_run_updated_at ON piflow_flow_run;
CREATE TRIGGER trg_piflow_flow_run_updated_at
BEFORE UPDATE ON piflow_flow_run
FOR EACH ROW
EXECUTE FUNCTION piflow_touch_updated_at();

DROP TRIGGER IF EXISTS trg_piflow_stop_job_run_updated_at ON piflow_stop_job_run;
CREATE TRIGGER trg_piflow_stop_job_run_updated_at
BEFORE UPDATE ON piflow_stop_job_run
FOR EACH ROW
EXECUTE FUNCTION piflow_touch_updated_at();

DROP TRIGGER IF EXISTS trg_piflow_batch_run_updated_at ON piflow_batch_run;
CREATE TRIGGER trg_piflow_batch_run_updated_at
BEFORE UPDATE ON piflow_batch_run
FOR EACH ROW
EXECUTE FUNCTION piflow_touch_updated_at();

DROP TRIGGER IF EXISTS trg_piflow_batch_item_run_updated_at ON piflow_batch_item_run;
CREATE TRIGGER trg_piflow_batch_item_run_updated_at
BEFORE UPDATE ON piflow_batch_item_run
FOR EACH ROW
EXECUTE FUNCTION piflow_touch_updated_at();
"""


def initialize_postgres_schema(connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute(PIFLOW_RUN_TRACKING_SCHEMA_SQL)
    connection.commit()
