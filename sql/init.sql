CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── dim_company: SCD Type 2 ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_company (
    company_key          SERIAL PRIMARY KEY,
    company_id           VARCHAR(100) NOT NULL,
    rated_entity         VARCHAR(255),
    corporate_sector     VARCHAR(100),
    reporting_currency   VARCHAR(20),
    country_of_origin    VARCHAR(100),
    accounting_principles VARCHAR(50),
    end_of_business_year VARCHAR(20),
    valid_from           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_to             TIMESTAMPTZ,
    is_current           BOOLEAN NOT NULL DEFAULT TRUE,
    version              INTEGER NOT NULL DEFAULT 1,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_dim_company_id      ON dim_company(company_id);
CREATE INDEX idx_dim_company_current ON dim_company(company_id, is_current);

-- ── dim_date ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_date (
    date_key    INTEGER PRIMARY KEY,  -- YYYYMMDD
    date_actual DATE NOT NULL,
    year        INTEGER, quarter INTEGER, month INTEGER,
    month_name  VARCHAR(20), week INTEGER, day_of_week INTEGER, is_weekend BOOLEAN
);
INSERT INTO dim_date
SELECT TO_CHAR(d,'YYYYMMDD')::INT, d::DATE,
       EXTRACT(YEAR FROM d)::INT, EXTRACT(QUARTER FROM d)::INT, EXTRACT(MONTH FROM d)::INT,
       TO_CHAR(d,'Month'), EXTRACT(WEEK FROM d)::INT, EXTRACT(DOW FROM d)::INT,
       EXTRACT(DOW FROM d) IN (0,6)
FROM generate_series('2010-01-01'::DATE,'2030-12-31'::DATE,'1 day') d
ON CONFLICT DO NOTHING;

-- ── fact_upload: audit trail of every file ────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_upload (
    upload_id           SERIAL PRIMARY KEY,
    upload_uuid         UUID NOT NULL DEFAULT gen_random_uuid(),
    source_filename     VARCHAR(255) NOT NULL,
    discussion_group    VARCHAR(10),
    discussion_version  VARCHAR(10),
    upload_timestamp    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    file_size_bytes     BIGINT,
    file_hash           VARCHAR(64),
    processing_status   VARCHAR(20) NOT NULL DEFAULT 'pending',
    error_message       TEXT,
    rows_extracted      INTEGER DEFAULT 0,
    processing_ms       INTEGER,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_upload_filename  ON fact_upload(source_filename);
CREATE INDEX idx_upload_hash      ON fact_upload(file_hash);
CREATE INDEX idx_upload_status    ON fact_upload(processing_status);
CREATE INDEX idx_upload_timestamp ON fact_upload(upload_timestamp);

-- ── fact_company_snapshot: one row per file per company ───────────────────────
CREATE TABLE IF NOT EXISTS fact_company_snapshot (
    snapshot_id          SERIAL PRIMARY KEY,
    snapshot_uuid        UUID NOT NULL DEFAULT gen_random_uuid(),
    company_key          INTEGER NOT NULL REFERENCES dim_company(company_key),
    upload_id            INTEGER NOT NULL REFERENCES fact_upload(upload_id),
    date_key             INTEGER NOT NULL REFERENCES dim_date(date_key),
    company_id           VARCHAR(100) NOT NULL,
    -- company info
    rated_entity         VARCHAR(255),
    corporate_sector     VARCHAR(100),
    -- reporting info
    reporting_currency   VARCHAR(20),
    country_of_origin    VARCHAR(100),
    accounting_principles VARCHAR(50),
    end_of_business_year VARCHAR(20),
    -- methodologies (stored as array)
    rating_methodologies JSONB,
    -- industry risk
    industry_risk        VARCHAR(100),
    industry_risk_score  VARCHAR(10),
    industry_weight      NUMERIC(6,4),
    segmentation_criteria VARCHAR(100),
    -- business risk
    business_risk_profile        VARCHAR(20),
    blended_industry_risk_profile VARCHAR(20),
    competitive_positioning       VARCHAR(20),
    market_share                  VARCHAR(20),
    diversification               VARCHAR(20),
    operating_profitability       VARCHAR(20),
    sector_specific_factor_1      VARCHAR(20),
    sector_specific_factor_2      VARCHAR(20),
    -- financial risk
    financial_risk_profile VARCHAR(20),
    leverage               VARCHAR(20),
    interest_cover         VARCHAR(20),
    cash_flow_cover        VARCHAR(20),
    fin_liquidity          VARCHAR(20),
    -- scope metrics stored as JSONB {metric: {year: value}}
    scope_metrics          JSONB,
    -- versioning
    version_number         INTEGER NOT NULL DEFAULT 1,
    is_latest              BOOLEAN NOT NULL DEFAULT TRUE,
    discussion_group       VARCHAR(10),
    discussion_version     VARCHAR(10),
    snapshot_timestamp     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- quality
    completeness_score     NUMERIC(5,2),
    has_validation_errors  BOOLEAN DEFAULT FALSE,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_snapshot_company_id ON fact_company_snapshot(company_id);
CREATE INDEX idx_snapshot_latest     ON fact_company_snapshot(company_id, is_latest);
CREATE INDEX idx_snapshot_timestamp  ON fact_company_snapshot(snapshot_timestamp);
CREATE INDEX idx_snapshot_upload     ON fact_company_snapshot(upload_id);
CREATE INDEX idx_snapshot_sector     ON fact_company_snapshot(corporate_sector);
CREATE INDEX idx_snapshot_country    ON fact_company_snapshot(country_of_origin);
CREATE INDEX idx_snapshot_currency   ON fact_company_snapshot(reporting_currency);

-- ── fact_scope_timeseries: one row per metric per year per snapshot ───────────
-- enables proper time-series queries on scope credit metrics
CREATE TABLE IF NOT EXISTS fact_scope_timeseries (
    id            SERIAL PRIMARY KEY,
    snapshot_id   INTEGER NOT NULL REFERENCES fact_company_snapshot(snapshot_id),
    company_id    VARCHAR(100) NOT NULL,
    upload_id     INTEGER NOT NULL,
    metric        VARCHAR(100) NOT NULL,
    year          VARCHAR(10) NOT NULL,
    value         NUMERIC(20,6),
    is_forecast   BOOLEAN NOT NULL DEFAULT FALSE,  -- TRUE for 2025E, 2026E etc
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_scope_company  ON fact_scope_timeseries(company_id);
CREATE INDEX idx_scope_metric   ON fact_scope_timeseries(metric);
CREATE INDEX idx_scope_year     ON fact_scope_timeseries(year);

-- ── validation_result ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS validation_result (
    id              SERIAL PRIMARY KEY,
    upload_id       INTEGER REFERENCES fact_upload(upload_id),
    company_id      VARCHAR(100),
    field_name      VARCHAR(100) NOT NULL,
    rule            VARCHAR(100) NOT NULL,
    is_valid        BOOLEAN NOT NULL,
    severity        VARCHAR(10) NOT NULL DEFAULT 'warning',
    message         TEXT,
    raw_value       TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_validation_upload  ON validation_result(upload_id);
CREATE INDEX idx_validation_valid   ON validation_result(is_valid);

-- ── pipeline_run ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pipeline_run (
    run_id           SERIAL PRIMARY KEY,
    started_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at     TIMESTAMPTZ,
    status           VARCHAR(20) NOT NULL DEFAULT 'running',
    files_discovered INTEGER DEFAULT 0,
    files_processed  INTEGER DEFAULT 0,
    files_skipped    INTEGER DEFAULT 0,
    files_failed     INTEGER DEFAULT 0,
    error_summary    TEXT,
    quality_report   JSONB
);

-- ── processed_file: incremental load dedup ────────────────────────────────────
CREATE TABLE IF NOT EXISTS processed_file (
    id           SERIAL PRIMARY KEY,
    filename     VARCHAR(255) NOT NULL UNIQUE,
    file_hash    VARCHAR(64) NOT NULL,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    upload_id    INTEGER REFERENCES fact_upload(upload_id)
);
CREATE INDEX idx_processed_hash ON processed_file(file_hash);

-- ── views for BI tools ────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_company_current AS
SELECT s.*, u.source_filename, u.upload_timestamp
FROM fact_company_snapshot s
JOIN fact_upload u ON s.upload_id = u.upload_id
WHERE s.is_latest = TRUE;

CREATE OR REPLACE VIEW vw_scope_timeseries AS
SELECT t.company_id, t.metric, t.year, t.value, t.is_forecast,
       s.rated_entity, s.corporate_sector, s.snapshot_timestamp
FROM fact_scope_timeseries t
JOIN fact_company_snapshot s ON t.snapshot_id = s.snapshot_id
WHERE s.is_latest = TRUE;
