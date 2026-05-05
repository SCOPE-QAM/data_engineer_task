-- One row per pipeline execution with summary statistics.
CREATE TABLE IF NOT EXISTS pipeline_run (
    run_id           SERIAL      PRIMARY KEY,
    started_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at     TIMESTAMPTZ,
    status           VARCHAR(20) NOT NULL DEFAULT 'running',
    files_discovered INTEGER     DEFAULT 0,
    files_processed  INTEGER     DEFAULT 0,
    files_skipped    INTEGER     DEFAULT 0,
    files_failed     INTEGER     DEFAULT 0,
    error_summary    TEXT,
    quality_report   JSONB
);
