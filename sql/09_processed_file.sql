-- Hash-based deduplication: prevents re-processing the same file.
CREATE TABLE IF NOT EXISTS processed_file (
    id           SERIAL      PRIMARY KEY,
    filename     VARCHAR(255) NOT NULL UNIQUE,
    file_hash    VARCHAR(64)  NOT NULL,
    processed_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    upload_id    INTEGER      REFERENCES fact_upload(upload_id)
);

CREATE INDEX idx_processed_hash ON processed_file(file_hash);
