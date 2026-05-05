-- Per-field validation issues recorded for every upload.
CREATE TABLE IF NOT EXISTS validation_result (
    id         SERIAL  PRIMARY KEY,
    upload_id  INTEGER REFERENCES fact_upload(upload_id),
    company_id VARCHAR(100),
    field_name VARCHAR(100) NOT NULL,
    rule       VARCHAR(100) NOT NULL,
    is_valid   BOOLEAN      NOT NULL,
    severity   VARCHAR(10)  NOT NULL DEFAULT 'warning',
    message    TEXT,
    raw_value  TEXT,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_validation_upload ON validation_result(upload_id);
CREATE INDEX idx_validation_valid  ON validation_result(is_valid);
