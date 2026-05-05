import os, uuid
from datetime import datetime, timezone

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from api.database import Base, get_db
from api.main import app
from api.models import (DimCompany, FactUpload, FactCompanySnapshot,
                        FactScopeTimeseries, ProcessedFile)
from pipeline.extractor import (
    MasterSheetData, CompanyInfo, IndustryRisk, ReportingInfo,
    BusinessRiskProfile, FinancialRiskProfile, ScopeCreditMetric, FileMetadata,
)

# ── database setup ────────────────────────────────────────────────────────────

engine = create_engine("sqlite:///./test.db", connect_args={"check_same_thread": False})
TestSession = sessionmaker(bind=engine)
app.dependency_overrides[get_db] = lambda: (s := TestSession(), s)[1]


@pytest.fixture(scope="session", autouse=True)
def setup():
    Base.metadata.create_all(engine)
    with engine.connect() as c:
        c.execute(text(
            "INSERT OR IGNORE INTO dim_date VALUES "
            "(20240101,'2024-01-01',2024,1,1,'January',1,1,0)"
        ))
        c.commit()
    yield
    Base.metadata.drop_all(engine)
    if os.path.exists("test.db"):
        os.remove("test.db")


@pytest.fixture
def db():
    s = TestSession()
    yield s
    s.rollback()
    s.close()


@pytest.fixture
def client():
    return TestClient(app)


# ── data builders ─────────────────────────────────────────────────────────────

def sample_data():
    return MasterSheetData(
        company_info=CompanyInfo(rated_entity="TestCo", corporate_sector="Industrials"),
        rating_methodologies=["Corporate Methodology"],
        industry_risk=IndustryRisk(
            industry_risk="Manufacturing", industry_risk_score="A",
            industry_weight=1.0, segmentation_criteria="EBITDA",
        ),
        reporting_info=ReportingInfo(
            reporting_currency="EUR", country_of_origin="Germany",
            accounting_principles="IFRS", end_of_business_year="December",
        ),
        business_risk=BusinessRiskProfile(business_risk_profile="B+"),
        financial_risk=FinancialRiskProfile(financial_risk_profile="C"),
        scope_metrics=[ScopeCreditMetric("EBITDA cover", {"2023": 4.5, "2024": 5.1, "2025E": 5.8})],
    )


def sample_meta(filename=None):
    filename = filename or f"corporates_A_{uuid.uuid4().hex[:6]}.xlsm"
    return FileMetadata(
        filepath=f"/tmp/{filename}", filename=filename,
        file_size_bytes=1024, file_hash=uuid.uuid4().hex,
        discussion_group="A", discussion_version="1",
    )


def seed(db, entity="SeedCo", is_latest=True, version=1):
    upload = FactUpload(
        upload_uuid=uuid.uuid4(),
        source_filename=f"{entity}_v{version}.xlsm",
        processing_status="success", rows_extracted=1,
    )
    db.add(upload)
    db.flush()
    dim = DimCompany(
        company_id=entity.lower(), rated_entity=entity,
        corporate_sector="Tech", is_current=is_latest, version=version,
    )
    db.add(dim)
    db.flush()
    snap = FactCompanySnapshot(
        snapshot_uuid=uuid.uuid4(), company_key=dim.company_key,
        upload_id=upload.upload_id, date_key=20240101,
        company_id=entity.lower(), rated_entity=entity,
        corporate_sector="Tech", reporting_currency="EUR",
        version_number=version, is_latest=is_latest,
        snapshot_timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        completeness_score=100.0, has_validation_errors=False,
    )
    db.add(snap)
    db.commit()
    return snap


def seed_scope(db, entity="ScopeSeed"):
    snap = seed(db, entity=entity)
    db.add(FactScopeTimeseries(
        snapshot_id=snap.snapshot_id, company_id=entity.lower(),
        upload_id=snap.upload_id, metric="EBITDA cover",
        year="2024", value=4.5, is_forecast=False,
    ))
    db.commit()
    return snap


def make_df():
    """Minimal 45×10 DataFrame matching the MASTER sheet layout."""
    data = [[None] * 10 for _ in range(45)]
    data[1][1] = "Rated entity";       data[1][2] = "ACME Corp"
    data[2][1] = "CorporateSector";    data[2][2] = "Industrials"
    data[4][2] = "Corp Methodology"
    data[6][1] = "Industry risk";           data[6][2] = "Manufacturing"
    data[7][1] = "Industry risk score";     data[7][2] = "A"
    data[8][1] = "Industry weight";         data[8][2] = 0.8
    data[9][1] = "Segmentation criteria";   data[9][2] = "EBITDA"
    data[11][1] = "Reporting Currency/Units"; data[11][2] = "EUR"
    data[12][1] = "Country of origin";        data[12][2] = "Germany"
    data[13][1] = "Accounting principles";    data[13][2] = "IFRS"
    data[14][1] = "End of business year";     data[14][2] = "December"
    data[17][1] = "Business risk profile";                   data[17][2] = "B+"
    data[18][1] = "(Blended) Industry risk profile";         data[18][2] = "B"
    data[19][1] = "Competitive Positioning";                 data[19][2] = "Strong"
    data[20][1] = "Market share";                            data[20][2] = "High"
    data[21][1] = "Diversification";                         data[21][2] = "Medium"
    data[22][1] = "Operating profitability";                 data[22][2] = "Good"
    data[23][1] = "Sector/company-specific factors (1)";     data[23][2] = "Factor1"
    data[24][1] = "Sector/company-specific factors (2)";     data[24][2] = "Factor2"
    data[26][1] = "Financial risk profile"; data[26][2] = "C"
    data[27][1] = "Leverage";               data[27][2] = "Medium"
    data[28][1] = "Interest cover";         data[28][2] = "Good"
    data[29][1] = "Cash flow cover";        data[29][2] = "Strong"
    data[30][1] = "Liquidity";              data[30][2] = "Adequate"
    data[34][2] = 2023;              data[34][3] = 2024; data[34][4] = "2025E"
    data[35][1] = "EBITDA cover";    data[35][2] = 4.5;  data[35][3] = 5.1; data[35][4] = 5.8
    data[36][1] = "Net debt/EBITDA"; data[36][2] = 2.1;  data[36][3] = 1.9
    return pd.DataFrame(data)
