-- Date dimension pre-seeded from 2010-01-01 to 2030-12-31.
CREATE TABLE IF NOT EXISTS dim_date (
    date_key    INTEGER PRIMARY KEY,  -- YYYYMMDD
    date_actual DATE    NOT NULL,
    year        INTEGER,
    quarter     INTEGER,
    month       INTEGER,
    month_name  VARCHAR(20),
    week        INTEGER,
    day_of_week INTEGER,
    is_weekend  BOOLEAN
);

INSERT INTO dim_date
SELECT
    TO_CHAR(d, 'YYYYMMDD')::INT,
    d::DATE,
    EXTRACT(YEAR    FROM d)::INT,
    EXTRACT(QUARTER FROM d)::INT,
    EXTRACT(MONTH   FROM d)::INT,
    TO_CHAR(d, 'Month'),
    EXTRACT(WEEK    FROM d)::INT,
    EXTRACT(DOW     FROM d)::INT,
    EXTRACT(DOW     FROM d) IN (0, 6)
FROM generate_series('2010-01-01'::DATE, '2030-12-31'::DATE, '1 day') d
ON CONFLICT DO NOTHING;
