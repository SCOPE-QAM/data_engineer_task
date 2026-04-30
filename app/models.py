from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Company(Base):
    __tablename__ = "dim_company"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    sector = Column(String)
    country = Column(String)


class Upload(Base):
    __tablename__ = "dim_upload"

    id = Column(Integer, primary_key=True)
    file_name = Column(String)
    file_hash = Column(String, unique=True)
    uploaded_at = Column(DateTime, default=func.now())


class Snapshot(Base):
    __tablename__ = "fact_snapshot"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("dim_company.id"))
    upload_id = Column(Integer, ForeignKey("dim_upload.id"))

    industry_score = Column(String)
    industry_weight = Column(Float)

    currency = Column(String)
    accounting = Column(String)
    year_end = Column(String)

    valid_from = Column(DateTime, default=func.now())
    valid_to = Column(DateTime, nullable=True)
    is_current = Column(Boolean, default=True)
