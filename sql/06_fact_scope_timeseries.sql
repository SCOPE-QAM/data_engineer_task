-- One row per metric per year per snapshot for time-series queries.
CREATE TABLE IF NOT EXISTS fact_scope_timeseries (
    id          SERIAL  PRIMARY KEY,
    snapshot_id INTEGER NOT NULL REFERENCES fact_company_snapshot(snapshot_id),
    company_id  VARCHAR(100) NOT NULL,
    upload_id   INTEGER NOT NULL,
    metric      VARCHAR(100) NOT NULL,
    year        VARCHAR(10)  NOT NULL,
    value       NUMERIC(20,6),
    is_forecast BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_scope_company ON fact_scope_timeseries(company_id);
CREATE INDEX idx_scope_metric  ON fact_scope_timeseries(metric);
CREATE INDEX idx_scope_year    ON fact_scope_timeseries(year);
