from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class _Base(BaseModel):
    model_config = ConfigDict(from_attributes=True)

# ── company ───────────────────────────────────────────────────────────────────
class CompanySummary(_Base):
    company_id: str
    rated_entity: Optional[str]
    corporate_sector: Optional[str]
    country_of_origin: Optional[str]
    reporting_currency: Optional[str]
    industry_risk_score: Optional[str]
    business_risk_profile: Optional[str]
    financial_risk_profile: Optional[str]
    version_number: int
    snapshot_timestamp: datetime
    completeness_score: Optional[float]
    has_validation_errors: bool

class CompanyDetail(CompanySummary):
    accounting_principles: Optional[str]
    end_of_business_year: Optional[str]
    rating_methodologies: Optional[list]
    industry_risk: Optional[str]
    industry_weight: Optional[float]
    segmentation_criteria: Optional[str]
    blended_industry_risk_profile: Optional[str]
    competitive_positioning: Optional[str]
    market_share: Optional[str]
    diversification: Optional[str]
    operating_profitability: Optional[str]
    sector_specific_factor_1: Optional[str]
    sector_specific_factor_2: Optional[str]
    leverage: Optional[str]
    interest_cover: Optional[str]
    cash_flow_cover: Optional[str]
    fin_liquidity: Optional[str]
    scope_metrics: Optional[dict]
    snapshot_id: int
    upload_id: int
    discussion_group: Optional[str]
    discussion_version: Optional[str]

class CompanyVersion(_Base):
    version_number: int
    snapshot_id: int
    snapshot_timestamp: datetime
    discussion_group: Optional[str]
    discussion_version: Optional[str]
    industry_risk_score: Optional[str]
    business_risk_profile: Optional[str]
    financial_risk_profile: Optional[str]
    source_filename: Optional[str] = None

class CompareResult(_Base):
    company_id: str
    rated_entity: Optional[str]
    corporate_sector: Optional[str]
    snapshot_timestamp: datetime
    version_number: int
    industry_risk_score: Optional[str]
    business_risk_profile: Optional[str]
    financial_risk_profile: Optional[str]

# ── scope timeseries ──────────────────────────────────────────────────────────
class ScopeTimeseriesPoint(_Base):
    metric: str
    year: str
    value: Optional[float]
    is_forecast: bool

# ── snapshot ──────────────────────────────────────────────────────────────────
class SnapshotSummary(_Base):
    snapshot_id: int
    company_id: str
    rated_entity: Optional[str]
    corporate_sector: Optional[str]
    version_number: int
    is_latest: bool
    snapshot_timestamp: datetime
    upload_id: int

class SnapshotDetail(SnapshotSummary):
    country_of_origin: Optional[str]
    reporting_currency: Optional[str]
    industry_risk_score: Optional[str]
    business_risk_profile: Optional[str]
    financial_risk_profile: Optional[str]
    scope_metrics: Optional[dict]
    completeness_score: Optional[float]
    has_validation_errors: bool
    discussion_group: Optional[str]
    discussion_version: Optional[str]

# ── upload ────────────────────────────────────────────────────────────────────
class UploadSummary(_Base):
    upload_id: int
    upload_uuid: UUID
    source_filename: str
    discussion_group: Optional[str]
    discussion_version: Optional[str]
    upload_timestamp: datetime
    processing_status: str
    rows_extracted: int
    processing_ms: Optional[int]
    file_size_bytes: Optional[int]

class UploadDetail(UploadSummary):
    file_hash: Optional[str]
    error_message: Optional[str]

class UploadStats(_Base):
    total_uploads: int
    successful: int
    failed: int
    total_companies: int
    total_snapshots: int
    latest_upload_at: Optional[datetime]

class ValidationIssue(_Base):
    id: int
    field_name: str
    rule: str
    is_valid: bool
    severity: str
    message: Optional[str]
    raw_value: Optional[str]

class HealthResponse(_Base):
    status: str
    database: str
    timestamp: datetime
