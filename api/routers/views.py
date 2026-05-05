from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
import os

from api.database import get_db
from api.models import FactCompanySnapshot, FactUpload, DimCompany, ValidationResult
from api.schemas import SnapshotSummary, SnapshotDetail, UploadSummary, UploadDetail, UploadStats, ValidationIssue

# ── snapshots ─────────────────────────────────────────────────────────────────
snapshots = APIRouter(prefix="/snapshots", tags=["snapshots"])

def _snap_detail(s): return SnapshotDetail(
    snapshot_id=s.snapshot_id, company_id=s.company_id, rated_entity=s.rated_entity,
    corporate_sector=s.corporate_sector, version_number=s.version_number,
    is_latest=s.is_latest, snapshot_timestamp=s.snapshot_timestamp, upload_id=s.upload_id,
    country_of_origin=s.country_of_origin, reporting_currency=s.reporting_currency,
    industry_risk_score=s.industry_risk_score, business_risk_profile=s.business_risk_profile,
    financial_risk_profile=s.financial_risk_profile, scope_metrics=s.scope_metrics,
    completeness_score=s.completeness_score, has_validation_errors=s.has_validation_errors,
    discussion_group=s.discussion_group, discussion_version=s.discussion_version)

@snapshots.get("", response_model=list[SnapshotSummary])
def list_snapshots(company_id: Optional[str] = None,
                   from_date: Optional[datetime] = None, to_date: Optional[datetime] = None,
                   sector: Optional[str] = None, country: Optional[str] = None,
                   currency: Optional[str] = None, skip: int = 0, limit: int = 50,
                   db: Session = Depends(get_db)):
    q = db.query(FactCompanySnapshot)
    if company_id: q = q.filter_by(company_id=company_id)
    if from_date:  q = q.filter(FactCompanySnapshot.snapshot_timestamp >= from_date)
    if to_date:    q = q.filter(FactCompanySnapshot.snapshot_timestamp <= to_date)
    if sector:     q = q.filter(FactCompanySnapshot.corporate_sector.ilike(f"%{sector}%"))
    if country:    q = q.filter(FactCompanySnapshot.country_of_origin.ilike(f"%{country}%"))
    if currency:   q = q.filter(FactCompanySnapshot.reporting_currency.ilike(f"%{currency}%"))
    rows = q.order_by(FactCompanySnapshot.snapshot_timestamp.desc()).offset(skip).limit(limit).all()
    return [SnapshotSummary(snapshot_id=s.snapshot_id, company_id=s.company_id,
                             rated_entity=s.rated_entity, corporate_sector=s.corporate_sector,
                             version_number=s.version_number, is_latest=s.is_latest,
                             snapshot_timestamp=s.snapshot_timestamp, upload_id=s.upload_id)
            for s in rows]

@snapshots.get("/latest", response_model=list[SnapshotDetail])
def latest_snapshots(db: Session = Depends(get_db)):
    rows = db.query(FactCompanySnapshot).filter_by(is_latest=True)\
             .order_by(FactCompanySnapshot.company_id).all()
    return [_snap_detail(s) for s in rows]

@snapshots.get("/{snapshot_id}", response_model=SnapshotDetail)
def get_snapshot(snapshot_id: int, db: Session = Depends(get_db)):
    s = db.query(FactCompanySnapshot).filter_by(snapshot_id=snapshot_id).first()
    if not s: raise HTTPException(404, f"Snapshot {snapshot_id} not found")
    return _snap_detail(s)


# ── uploads ───────────────────────────────────────────────────────────────────
uploads = APIRouter(prefix="/uploads", tags=["uploads"])

@uploads.get("", response_model=list[UploadSummary])
def list_uploads(status: Optional[str] = None,
                 from_date: Optional[datetime] = None, to_date: Optional[datetime] = None,
                 skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    q = db.query(FactUpload)
    if status:    q = q.filter_by(processing_status=status)
    if from_date: q = q.filter(FactUpload.upload_timestamp >= from_date)
    if to_date:   q = q.filter(FactUpload.upload_timestamp <= to_date)
    rows = q.order_by(FactUpload.upload_timestamp.desc()).offset(skip).limit(limit).all()
    return [UploadSummary(upload_id=u.upload_id, upload_uuid=u.upload_uuid,
                           source_filename=u.source_filename, discussion_group=u.discussion_group,
                           discussion_version=u.discussion_version, upload_timestamp=u.upload_timestamp,
                           processing_status=u.processing_status, rows_extracted=u.rows_extracted,
                           processing_ms=u.processing_ms, file_size_bytes=u.file_size_bytes)
            for u in rows]

@uploads.get("/stats", response_model=UploadStats)
def upload_stats(db: Session = Depends(get_db)):
    return UploadStats(
        total_uploads=db.query(func.count(FactUpload.upload_id)).scalar() or 0,
        successful=db.query(func.count(FactUpload.upload_id)).filter_by(processing_status="success").scalar() or 0,
        failed=db.query(func.count(FactUpload.upload_id)).filter_by(processing_status="failed").scalar() or 0,
        total_companies=db.query(func.count(DimCompany.company_key)).filter_by(is_current=True).scalar() or 0,
        total_snapshots=db.query(func.count(FactCompanySnapshot.snapshot_id)).scalar() or 0,
        latest_upload_at=db.query(func.max(FactUpload.upload_timestamp)).scalar(),
    )

@uploads.get("/{upload_id}/details", response_model=UploadDetail)
def upload_details(upload_id: int, db: Session = Depends(get_db)):
    u = db.query(FactUpload).filter_by(upload_id=upload_id).first()
    if not u: raise HTTPException(404, f"Upload {upload_id} not found")
    return UploadDetail(upload_id=u.upload_id, upload_uuid=u.upload_uuid,
                        source_filename=u.source_filename, discussion_group=u.discussion_group,
                        discussion_version=u.discussion_version, upload_timestamp=u.upload_timestamp,
                        processing_status=u.processing_status, rows_extracted=u.rows_extracted,
                        processing_ms=u.processing_ms, file_size_bytes=u.file_size_bytes,
                        file_hash=u.file_hash, error_message=u.error_message)

@uploads.get("/{upload_id}/file")
def download_file(upload_id: int, db: Session = Depends(get_db)):
    u = db.query(FactUpload).filter_by(upload_id=upload_id).first()
    if not u: raise HTTPException(404, "Upload not found")
    if not u.source_filename or not os.path.exists(u.source_filename):
        raise HTTPException(404, "File not available on disk")
    return FileResponse(u.source_filename, filename=os.path.basename(u.source_filename))

@uploads.get("/{upload_id}/validations", response_model=list[ValidationIssue])
def upload_validations(upload_id: int, db: Session = Depends(get_db)):
    rows = db.query(ValidationResult).filter_by(upload_id=upload_id).all()
    return [ValidationIssue(id=v.id, field_name=v.field_name, rule=v.rule,
                             is_valid=v.is_valid, severity=v.severity,
                             message=v.message, raw_value=v.raw_value) for v in rows]
