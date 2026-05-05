-- SCD Type 2 company dimension: one row per version of a company's attributes.
CREATE TABLE IF NOT EXISTS dim_company (
    company_key           SERIAL PRIMARY KEY,
    company_id            VARCHAR(100) NOT NULL,
    rated_entity          VARCHAR(255),
    corporate_sector      VARCHAR(100),
    reporting_currency    VARCHAR(20),
    country_of_origin     VARCHAR(100),
    accounting_principles VARCHAR(50),
    end_of_business_year  VARCHAR(20),
    valid_from            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_to              TIMESTAMPTZ,
    is_current            BOOLEAN     NOT NULL DEFAULT TRUE,
    version               INTEGER     NOT NULL DEFAULT 1,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_dim_company_id      ON dim_company(company_id);
CREATE INDEX idx_dim_company_current ON dim_company(company_id, is_current);
