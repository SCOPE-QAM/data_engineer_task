from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from api.database import get_db
from api.models import FactCompanySnapshot, FactUpload, FactScopeTimeseries
from api.schemas import CompanySummary, CompanyDetail, CompanyVersion, CompareResult, ScopeTimeseriesPoint

router = APIRouter(prefix="/companies", tags=["companies"])

def _to_summary(s): return CompanySummary(
    company_id=s.company_id, rated_entity=s.rated_entity,
    corporate_sector=s.corporate_sector, country_of_origin=s.country_of_origin,
    reporting_currency=s.reporting_currency, industry_risk_score=s.industry_risk_score,
    business_risk_profile=s.business_risk_profile, financial_risk_profile=s.financial_risk_profile,
    version_number=s.version_number, snapshot_timestamp=s.snapshot_timestamp,
    completeness_score=s.completeness_score, has_validation_errors=s.has_validation_errors)

def _to_detail(s, filename=None): return CompanyDetail(
    **_to_summary(s).__dict__,
    accounting_principles=s.accounting_principles, end_of_business_year=s.end_of_business_year,
    rating_methodologies=s.rating_methodologies, industry_risk=s.industry_risk,
    industry_weight=float(s.industry_weight) if s.industry_weight else None,
    segmentation_criteria=s.segmentation_criteria,
    blended_industry_risk_profile=s.blended_industry_risk_profile,
    competitive_positioning=s.competitive_positioning, market_share=s.market_share,
    diversification=s.diversification, operating_profitability=s.operating_profitability,
    sector_specific_factor_1=s.sector_specific_factor_1,
    sector_specific_factor_2=s.sector_specific_factor_2,
    leverage=s.leverage, interest_cover=s.interest_cover,
    cash_flow_cover=s.cash_flow_cover, fin_liquidity=s.fin_liquidity,
    scope_metrics=s.scope_metrics, snapshot_id=s.snapshot_id, upload_id=s.upload_id,
    discussion_group=s.discussion_group, discussion_version=s.discussion_version)


@router.get("", response_model=list[CompanySummary])
def list_companies(
    sector: Optional[str] = None, country: Optional[str] = None,
    currency: Optional[str] = None, skip: int = 0, limit: int = 50,
    db: Session = Depends(get_db)):
    q = db.query(FactCompanySnapshot).filter_by(is_latest=True)
    if sector:   q = q.filter(FactCompanySnapshot.corporate_sector.ilike(f"%{sector}%"))
    if country:  q = q.filter(FactCompanySnapshot.country_of_origin.ilike(f"%{country}%"))
    if currency: q = q.filter(FactCompanySnapshot.reporting_currency.ilike(f"%{currency}%"))
    return [_to_summary(s) for s in q.order_by(FactCompanySnapshot.company_id).offset(skip).limit(limit)]


@router.get("/compare", response_model=list[CompareResult])
def compare_companies(
    company_ids: str = Query(...), as_of_date: Optional[datetime] = None,
    db: Session = Depends(get_db)):
    ids = [c.strip() for c in company_ids.split(",") if c.strip()]
    if not ids: raise HTTPException(400, "company_ids required")
    as_of = as_of_date or datetime.now(timezone.utc)
    results = []
    for cid in ids:
        s = db.query(FactCompanySnapshot)\
              .filter(FactCompanySnapshot.company_id == cid,
                      FactCompanySnapshot.snapshot_timestamp <= as_of)\
              .order_by(FactCompanySnapshot.snapshot_timestamp.desc()).first()
        if s:
            results.append(CompareResult(
                company_id=s.company_id, rated_entity=s.rated_entity,
                corporate_sector=s.corporate_sector, snapshot_timestamp=s.snapshot_timestamp,
                version_number=s.version_number, industry_risk_score=s.industry_risk_score,
                business_risk_profile=s.business_risk_profile,
                financial_risk_profile=s.financial_risk_profile))
    return results


@router.get("/{company_id}", response_model=CompanyDetail)
def get_company(company_id: str, db: Session = Depends(get_db)):
    s = db.query(FactCompanySnapshot).filter_by(company_id=company_id, is_latest=True).first()
    if not s: raise HTTPException(404, f"Company '{company_id}' not found")
    return _to_detail(s)


@router.get("/{company_id}/versions", response_model=list[CompanyVersion])
def get_versions(company_id: str, db: Session = Depends(get_db)):
    rows = db.query(FactCompanySnapshot, FactUpload.source_filename)\
             .join(FactUpload, FactCompanySnapshot.upload_id == FactUpload.upload_id)\
             .filter(FactCompanySnapshot.company_id == company_id)\
             .order_by(FactCompanySnapshot.version_number).all()
    if not rows: raise HTTPException(404, f"No versions for '{company_id}'")
    return [CompanyVersion(
        version_number=s.version_number, snapshot_id=s.snapshot_id,
        snapshot_timestamp=s.snapshot_timestamp, discussion_group=s.discussion_group,
        discussion_version=s.discussion_version, industry_risk_score=s.industry_risk_score,
        business_risk_profile=s.business_risk_profile,
        financial_risk_profile=s.financial_risk_profile, source_filename=fn)
        for s, fn in rows]


@router.get("/{company_id}/history", response_model=list[CompanyVersion])
def get_history(company_id: str,
                from_date: Optional[datetime] = None, to_date: Optional[datetime] = None,
                db: Session = Depends(get_db)):
    q = db.query(FactCompanySnapshot, FactUpload.source_filename)\
          .join(FactUpload, FactCompanySnapshot.upload_id == FactUpload.upload_id)\
          .filter(FactCompanySnapshot.company_id == company_id)
    if from_date: q = q.filter(FactCompanySnapshot.snapshot_timestamp >= from_date)
    if to_date:   q = q.filter(FactCompanySnapshot.snapshot_timestamp <= to_date)
    rows = q.order_by(FactCompanySnapshot.snapshot_timestamp).all()
    if not rows: raise HTTPException(404, f"No history for '{company_id}'")
    return [CompanyVersion(
        version_number=s.version_number, snapshot_id=s.snapshot_id,
        snapshot_timestamp=s.snapshot_timestamp, discussion_group=s.discussion_group,
        discussion_version=s.discussion_version, industry_risk_score=s.industry_risk_score,
        business_risk_profile=s.business_risk_profile,
        financial_risk_profile=s.financial_risk_profile, source_filename=fn)
        for s, fn in rows]


@router.get("/{company_id}/scope", response_model=list[ScopeTimeseriesPoint])
def get_scope_timeseries(company_id: str, metric: Optional[str] = None,
                         db: Session = Depends(get_db)):
    """Requirement #6 - time series data for Scope Credit Metrics."""
    q = db.query(FactScopeTimeseries)\
          .join(FactCompanySnapshot, FactScopeTimeseries.snapshot_id == FactCompanySnapshot.snapshot_id)\
          .filter(FactCompanySnapshot.company_id == company_id, FactCompanySnapshot.is_latest == True)
    if metric: q = q.filter(FactScopeTimeseries.metric.ilike(f"%{metric}%"))
    rows = q.order_by(FactScopeTimeseries.metric, FactScopeTimeseries.year).all()
    if not rows: raise HTTPException(404, f"No scope metrics for '{company_id}'")
    return [ScopeTimeseriesPoint(metric=r.metric, year=r.year,
                                  value=float(r.value) if r.value else None,
                                  is_forecast=r.is_forecast) for r in rows]
