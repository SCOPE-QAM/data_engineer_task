-- vw_company_current: latest snapshot for every active company.
CREATE OR REPLACE VIEW vw_company_current AS
SELECT s.*, u.source_filename, u.upload_timestamp
FROM   fact_company_snapshot s
JOIN   fact_upload u ON s.upload_id = u.upload_id
WHERE  s.is_latest = TRUE;

-- vw_scope_timeseries: scope metrics joined to their latest snapshot context.
CREATE OR REPLACE VIEW vw_scope_timeseries AS
SELECT t.company_id, t.metric, t.year, t.value, t.is_forecast,
       s.rated_entity, s.corporate_sector, s.snapshot_timestamp
FROM   fact_scope_timeseries t
JOIN   fact_company_snapshot s ON t.snapshot_id = s.snapshot_id
WHERE  s.is_latest = TRUE;
