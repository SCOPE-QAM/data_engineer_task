import re, time
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from api.models import (DimCompany, FactUpload, FactCompanySnapshot,
                           FactScopeTimeseries, ValidationResult, ProcessedFile)
from .extractor import FileMetadata, MasterSheetData
from .validator import validate, completeness

def _now(): return datetime.now(timezone.utc)
def _date_key(dt): return int(dt.strftime("%Y%m%d"))
def _company_id(name): return re.sub(r"[^a-z0-9]+", "_", name.lower().strip()).strip("_")


def is_processed(session: Session, filename: str, file_hash: str) -> bool:
    return session.query(ProcessedFile).filter_by(filename=filename, file_hash=file_hash).first() is not None


def _upsert_dim(session: Session, meta: FileMetadata, data: MasterSheetData) -> DimCompany:
    """SCD Type 2 upsert."""
    cid = _company_id(data.company_info.rated_entity or "unknown")
    now = _now()
    current = session.query(DimCompany).filter_by(company_id=cid, is_current=True).first()

    changed = current and (
        current.corporate_sector     != data.company_info.corporate_sector or
        current.reporting_currency   != data.reporting_info.reporting_currency or
        current.country_of_origin    != data.reporting_info.country_of_origin or
        current.accounting_principles!= data.reporting_info.accounting_principles
    )

    if current and not changed:
        return current

    if changed:
        current.valid_to = now
        current.is_current = False

    new = DimCompany(
        company_id=cid,
        rated_entity=data.company_info.rated_entity,
        corporate_sector=data.company_info.corporate_sector,
        reporting_currency=data.reporting_info.reporting_currency,
        country_of_origin=data.reporting_info.country_of_origin,
        accounting_principles=data.reporting_info.accounting_principles,
        end_of_business_year=data.reporting_info.end_of_business_year,
        valid_from=now, is_current=True,
        version=(current.version + 1) if changed else 1,
    )
    session.add(new)
    session.flush()
    return new


def load_file(session: Session, meta: FileMetadata, data: MasterSheetData,
              run_id: Optional[int] = None, force: bool = False) -> Optional[FactUpload]:

    if not force and is_processed(session, meta.filename, meta.file_hash):
        return None

    t0 = time.monotonic()
    upload = FactUpload(
        source_filename=meta.filename,
        discussion_group=meta.discussion_group,
        discussion_version=meta.discussion_version,
        file_size_bytes=meta.file_size_bytes,
        file_hash=meta.file_hash,
        processing_status="pending",
    )
    session.add(upload)
    session.flush()

    try:
        # validate
        report = validate(data)
        score  = completeness(data)

        for issue in report.issues:
            session.add(ValidationResult(
                upload_id=upload.upload_id, company_id=data.company_info.rated_entity,
                field_name=issue.field_name, rule=issue.rule, is_valid=issue.is_valid,
                severity=issue.severity, message=issue.message, raw_value=issue.raw_value,
            ))

        # dim company SCD2
        dim = _upsert_dim(session, meta, data)
        cid = dim.company_id

        # retire old latest snapshots
        session.query(FactCompanySnapshot).filter_by(company_id=cid, is_latest=True)\
               .update({"is_latest": False}, synchronize_session="fetch")

        # version number
        max_v = session.query(func.max(FactCompanySnapshot.version_number))\
                       .filter_by(company_id=cid).scalar() or 0
        now = _now()

        # build scope_metrics JSONB {metric: {year: value}}
        scope_json = {m.metric: m.values for m in data.scope_metrics}

        snap = FactCompanySnapshot(
            company_key=dim.company_key, upload_id=upload.upload_id,
            date_key=_date_key(now), company_id=cid,
            rated_entity=data.company_info.rated_entity,
            corporate_sector=data.company_info.corporate_sector,
            reporting_currency=data.reporting_info.reporting_currency,
            country_of_origin=data.reporting_info.country_of_origin,
            accounting_principles=data.reporting_info.accounting_principles,
            end_of_business_year=data.reporting_info.end_of_business_year,
            rating_methodologies=data.rating_methodologies,
            industry_risk=data.industry_risk.industry_risk,
            industry_risk_score=data.industry_risk.industry_risk_score,
            industry_weight=data.industry_risk.industry_weight,
            segmentation_criteria=data.industry_risk.segmentation_criteria,
            business_risk_profile=data.business_risk.business_risk_profile,
            blended_industry_risk_profile=data.business_risk.blended_industry_risk_profile,
            competitive_positioning=data.business_risk.competitive_positioning,
            market_share=data.business_risk.market_share,
            diversification=data.business_risk.diversification,
            operating_profitability=data.business_risk.operating_profitability,
            sector_specific_factor_1=data.business_risk.sector_specific_factor_1,
            sector_specific_factor_2=data.business_risk.sector_specific_factor_2,
            financial_risk_profile=data.financial_risk.financial_risk_profile,
            leverage=data.financial_risk.leverage,
            interest_cover=data.financial_risk.interest_cover,
            cash_flow_cover=data.financial_risk.cash_flow_cover,
            fin_liquidity=data.financial_risk.liquidity,
            scope_metrics=scope_json,
            version_number=max_v + 1, is_latest=True,
            discussion_group=meta.discussion_group,
            discussion_version=meta.discussion_version,
            snapshot_timestamp=now,
            completeness_score=score,
            has_validation_errors=report.has_errors,
        )
        session.add(snap)
        session.flush()

        # expand scope metrics into timeseries rows
        for m in data.scope_metrics:
            for year, value in m.values.items():
                session.add(FactScopeTimeseries(
                    snapshot_id=snap.snapshot_id, company_id=cid,
                    upload_id=upload.upload_id, metric=m.metric,
                    year=year, value=value,
                    is_forecast=any(year.endswith(s) for s in ("E","F","f","e")),
                ))

        upload.processing_status = "success"
        upload.rows_extracted = 1
        upload.processing_ms = int((time.monotonic() - t0) * 1000)

        # mark processed
        pf = session.query(ProcessedFile).filter_by(filename=meta.filename).first()
        if pf:
            pf.file_hash = meta.file_hash; pf.upload_id = upload.upload_id
        else:
            session.add(ProcessedFile(filename=meta.filename, file_hash=meta.file_hash, upload_id=upload.upload_id))

        session.flush()
        return upload

    except Exception as exc:
        upload.processing_status = "failed"
        upload.error_message = str(exc)
        session.flush()
        raise
