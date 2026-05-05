-- Audit trail of every .xlsm file submitted to the pipeline.
CREATE TABLE IF NOT EXISTS fact_upload (
    upload_id          SERIAL      PRIMARY KEY,
    upload_uuid        UUID        NOT NULL DEFAULT gen_random_uuid(),
    source_filename    VARCHAR(255) NOT NULL,
    discussion_group   VARCHAR(10),
    discussion_version VARCHAR(10),
    upload_timestamp   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    file_size_bytes    BIGINT,
    file_hash          VARCHAR(64),
    processing_status  VARCHAR(20) NOT NULL DEFAULT 'pending',
    error_message      TEXT,
    rows_extracted     INTEGER     DEFAULT 0,
    processing_ms      INTEGER,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_upload_filename  ON fact_upload(source_filename);
CREATE INDEX idx_upload_hash      ON fact_upload(file_hash);
CREATE INDEX idx_upload_status    ON fact_upload(processing_status);
CREATE INDEX idx_upload_timestamp ON fact_upload(upload_timestamp);
