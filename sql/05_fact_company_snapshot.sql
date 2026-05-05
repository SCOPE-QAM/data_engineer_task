-- One row per file per company: full attribute snapshot at upload time.
CREATE TABLE IF NOT EXISTS fact_company_snapshot (
    snapshot_id   SERIAL PRIMARY KEY,
    snapshot_uuid UUID   NOT NULL DEFAULT gen_random_uuid(),
    company_key   INTEGER     NOT NULL REFERENCES dim_company(company_key),
    upload_id     INTEGER     NOT NULL REFERENCES fact_upload(upload_id),
    date_key      INTEGER     NOT NULL REFERENCES dim_date(date_key),
    company_id    VARCHAR(100) NOT NULL,

    -- company info
    rated_entity          VARCHAR(255),
    corporate_sector      VARCHAR(100),

    -- reporting info
    reporting_currency    VARCHAR(20),
    country_of_origin     VARCHAR(100),
    accounting_principles VARCHAR(50),
    end_of_business_year  VARCHAR(20),

    -- methodologies
    rating_methodologies  JSONB,

    -- industry risk
    industry_risk         VARCHAR(100),
    industry_risk_score   VARCHAR(10),
    industry_weight       NUMERIC(6,4),
    segmentation_criteria VARCHAR(100),

    -- business risk
    business_risk_profile         VARCHAR(20),
    blended_industry_risk_profile  VARCHAR(20),
    competitive_positioning        VARCHAR(20),
    market_share                   VARCHAR(20),
    diversification                VARCHAR(20),
    operating_profitability        VARCHAR(20),
    sector_specific_factor_1       VARCHAR(20),
    sector_specific_factor_2       VARCHAR(20),

    -- financial risk
    financial_risk_profile VARCHAR(20),
    leverage               VARCHAR(20),
    interest_cover         VARCHAR(20),
    cash_flow_cover        VARCHAR(20),
    fin_liquidity          VARCHAR(20),

    -- scope metrics {metric: {year: value}}
    scope_metrics          JSONB,

    -- versioning & quality
    version_number         INTEGER     NOT NULL DEFAULT 1,
    is_latest              BOOLEAN     NOT NULL DEFAULT TRUE,
    discussion_group       VARCHAR(10),
    discussion_version     VARCHAR(10),
    snapshot_timestamp     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completeness_score     NUMERIC(5,2),
    has_validation_errors  BOOLEAN     DEFAULT FALSE,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_snapshot_company_id ON fact_company_snapshot(company_id);
CREATE INDEX idx_snapshot_latest     ON fact_company_snapshot(company_id, is_latest);
CREATE INDEX idx_snapshot_timestamp  ON fact_company_snapshot(snapshot_timestamp);
CREATE INDEX idx_snapshot_upload     ON fact_company_snapshot(upload_id);
CREATE INDEX idx_snapshot_sector     ON fact_company_snapshot(corporate_sector);
CREATE INDEX idx_snapshot_country    ON fact_company_snapshot(country_of_origin);
CREATE INDEX idx_snapshot_currency   ON fact_company_snapshot(reporting_currency);
