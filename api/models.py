import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

def _now(): return datetime.now(timezone.utc)

class DimCompany(Base):
    __tablename__ = "dim_company"
    company_key:          Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id:           Mapped[str]           = mapped_column(String(100), nullable=False)
    rated_entity:         Mapped[Optional[str]] = mapped_column(String(255))
    corporate_sector:     Mapped[Optional[str]] = mapped_column(String(100))
    reporting_currency:   Mapped[Optional[str]] = mapped_column(String(20))
    country_of_origin:    Mapped[Optional[str]] = mapped_column(String(100))
    accounting_principles:Mapped[Optional[str]] = mapped_column(String(50))
    end_of_business_year: Mapped[Optional[str]] = mapped_column(String(20))
    valid_from:           Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=_now)
    valid_to:             Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_current:           Mapped[bool]          = mapped_column(Boolean, default=True)
    version:              Mapped[int]           = mapped_column(Integer, default=1)
    created_at:           Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=_now)
    snapshots: Mapped[list["FactCompanySnapshot"]] = relationship(back_populates="company")

class FactUpload(Base):
    __tablename__ = "fact_upload"
    upload_id:          Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    upload_uuid:        Mapped[uuid.UUID]     = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, unique=True)
    source_filename:    Mapped[str]           = mapped_column(String(255), nullable=False)
    discussion_group:   Mapped[Optional[str]] = mapped_column(String(10))
    discussion_version: Mapped[Optional[str]] = mapped_column(String(10))
    upload_timestamp:   Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=_now)
    file_size_bytes:    Mapped[Optional[int]] = mapped_column(BigInteger)
    file_hash:          Mapped[Optional[str]] = mapped_column(String(64))
    processing_status:  Mapped[str]           = mapped_column(String(20), default="pending")
    error_message:      Mapped[Optional[str]] = mapped_column(Text)
    rows_extracted:     Mapped[int]           = mapped_column(Integer, default=0)
    processing_ms:      Mapped[Optional[int]] = mapped_column(Integer)
    created_at:         Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=_now)
    snapshots:    Mapped[list["FactCompanySnapshot"]] = relationship(back_populates="upload")
    validations:  Mapped[list["ValidationResult"]]   = relationship(back_populates="upload")

class FactCompanySnapshot(Base):
    __tablename__ = "fact_company_snapshot"
    snapshot_id:          Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_uuid:        Mapped[uuid.UUID]     = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, unique=True)
    company_key:          Mapped[int]           = mapped_column(Integer, ForeignKey("dim_company.company_key"))
    upload_id:            Mapped[int]           = mapped_column(Integer, ForeignKey("fact_upload.upload_id"))
    date_key:             Mapped[int]           = mapped_column(Integer, ForeignKey("dim_date.date_key"))
    company_id:           Mapped[str]           = mapped_column(String(100), nullable=False)
    rated_entity:         Mapped[Optional[str]] = mapped_column(String(255))
    corporate_sector:     Mapped[Optional[str]] = mapped_column(String(100))
    reporting_currency:   Mapped[Optional[str]] = mapped_column(String(20))
    country_of_origin:    Mapped[Optional[str]] = mapped_column(String(100))
    accounting_principles:Mapped[Optional[str]] = mapped_column(String(50))
    end_of_business_year: Mapped[Optional[str]] = mapped_column(String(20))
    rating_methodologies: Mapped[Optional[list]] = mapped_column(JSON(none_as_null=True))
    industry_risk:        Mapped[Optional[str]] = mapped_column(String(100))
    industry_risk_score:  Mapped[Optional[str]] = mapped_column(String(10))
    industry_weight:      Mapped[Optional[float]] = mapped_column(Numeric(6,4))
    segmentation_criteria:Mapped[Optional[str]] = mapped_column(String(100))
    business_risk_profile:        Mapped[Optional[str]] = mapped_column(String(20))
    blended_industry_risk_profile:Mapped[Optional[str]] = mapped_column(String(20))
    competitive_positioning:      Mapped[Optional[str]] = mapped_column(String(20))
    market_share:                 Mapped[Optional[str]] = mapped_column(String(20))
    diversification:              Mapped[Optional[str]] = mapped_column(String(20))
    operating_profitability:      Mapped[Optional[str]] = mapped_column(String(20))
    sector_specific_factor_1:     Mapped[Optional[str]] = mapped_column(String(20))
    sector_specific_factor_2:     Mapped[Optional[str]] = mapped_column(String(20))
    financial_risk_profile:       Mapped[Optional[str]] = mapped_column(String(20))
    leverage:                     Mapped[Optional[str]] = mapped_column(String(20))
    interest_cover:               Mapped[Optional[str]] = mapped_column(String(20))
    cash_flow_cover:              Mapped[Optional[str]] = mapped_column(String(20))
    fin_liquidity:                Mapped[Optional[str]] = mapped_column(String(20))
    scope_metrics:                Mapped[Optional[dict]] = mapped_column(JSON)
    version_number:    Mapped[int]           = mapped_column(Integer, default=1)
    is_latest:         Mapped[bool]          = mapped_column(Boolean, default=True)
    discussion_group:  Mapped[Optional[str]] = mapped_column(String(10))
    discussion_version:Mapped[Optional[str]] = mapped_column(String(10))
    snapshot_timestamp:Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=_now)
    completeness_score:Mapped[Optional[float]] = mapped_column(Numeric(5,2))
    has_validation_errors: Mapped[bool]      = mapped_column(Boolean, default=False)
    created_at:        Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=_now)
    company: Mapped["DimCompany"] = relationship(back_populates="snapshots")
    upload:  Mapped["FactUpload"] = relationship(back_populates="snapshots")
    scope_timeseries: Mapped[list["FactScopeTimeseries"]] = relationship(back_populates="snapshot")

class FactScopeTimeseries(Base):
    __tablename__ = "fact_scope_timeseries"
    id:          Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[int]           = mapped_column(Integer, ForeignKey("fact_company_snapshot.snapshot_id"))
    company_id:  Mapped[str]           = mapped_column(String(100), nullable=False)
    upload_id:   Mapped[int]           = mapped_column(Integer, nullable=False)
    metric:      Mapped[str]           = mapped_column(String(100), nullable=False)
    year:        Mapped[str]           = mapped_column(String(10), nullable=False)
    value:       Mapped[Optional[float]] = mapped_column(Numeric(20,6))
    is_forecast: Mapped[bool]          = mapped_column(Boolean, default=False)
    created_at:  Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=_now)
    snapshot: Mapped["FactCompanySnapshot"] = relationship(back_populates="scope_timeseries")

class DimDate(Base):
    __tablename__ = "dim_date"
    date_key:    Mapped[int]  = mapped_column(Integer, primary_key=True)
    date_actual: Mapped[datetime] = mapped_column(DateTime(timezone=False))
    year:        Mapped[int]  = mapped_column(Integer)
    quarter:     Mapped[int]  = mapped_column(Integer)
    month:       Mapped[int]  = mapped_column(Integer)
    month_name:  Mapped[str]  = mapped_column(String(20))
    week:        Mapped[int]  = mapped_column(Integer)
    day_of_week: Mapped[int]  = mapped_column(Integer)
    is_weekend:  Mapped[bool] = mapped_column(Boolean)

class ValidationResult(Base):
    __tablename__ = "validation_result"
    id:         Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    upload_id:  Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("fact_upload.upload_id"))
    company_id: Mapped[Optional[str]] = mapped_column(String(100))
    field_name: Mapped[str]           = mapped_column(String(100), nullable=False)
    rule:       Mapped[str]           = mapped_column(String(100), nullable=False)
    is_valid:   Mapped[bool]          = mapped_column(Boolean, nullable=False)
    severity:   Mapped[str]           = mapped_column(String(10), default="warning")
    message:    Mapped[Optional[str]] = mapped_column(Text)
    raw_value:  Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=_now)
    upload: Mapped[Optional["FactUpload"]] = relationship(back_populates="validations")

class PipelineRun(Base):
    __tablename__ = "pipeline_run"
    run_id:           Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    started_at:       Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=_now)
    completed_at:     Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status:           Mapped[str]           = mapped_column(String(20), default="running")
    files_discovered: Mapped[int]           = mapped_column(Integer, default=0)
    files_processed:  Mapped[int]           = mapped_column(Integer, default=0)
    files_skipped:    Mapped[int]           = mapped_column(Integer, default=0)
    files_failed:     Mapped[int]           = mapped_column(Integer, default=0)
    error_summary:    Mapped[Optional[str]] = mapped_column(Text)
    quality_report:   Mapped[Optional[dict]] = mapped_column(JSON)

class ProcessedFile(Base):
    __tablename__ = "processed_file"
    id:           Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename:     Mapped[str]      = mapped_column(String(255), unique=True, nullable=False)
    file_hash:    Mapped[str]      = mapped_column(String(64), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    upload_id:    Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("fact_upload.upload_id"))
