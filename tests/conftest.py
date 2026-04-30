import os
import sys
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.routes import get_db
from app.db import SessionLocal, engine
from app.main import app
from app.models import Base, Company, Snapshot, Upload

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = f"sqlite:///{ROOT / 'test.db'}"


@pytest.fixture(autouse=True)
def clean_db():
    """Reset the test database before and after each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Provide a database session for a test case."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """Provide a FastAPI test client bound to the test session."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def seeded_data(db_session):
    """Insert a company with two uploads and two snapshots."""
    company = Company(name="Alpha Corp", sector="Utilities", country="DE")
    db_session.add(company)
    db_session.commit()

    upload_1 = Upload(file_name="alpha_v1.xlsm", file_hash="hash-1")
    upload_2 = Upload(file_name="alpha_v2.xlsm", file_hash="hash-2")
    db_session.add_all([upload_1, upload_2])
    db_session.commit()

    snapshot_1 = Snapshot(
        company_id=company.id,
        upload_id=upload_1.id,
        industry_score="A",
        industry_weight=0.4,
        currency="EUR",
        accounting="IFRS",
        year_end="December",
        is_current=False,
        valid_to=datetime(2024, 1, 1),
    )
    snapshot_2 = Snapshot(
        company_id=company.id,
        upload_id=upload_2.id,
        industry_score="BBB",
        industry_weight=0.6,
        currency="EUR",
        accounting="IFRS",
        year_end="December",
        is_current=True,
    )
    db_session.add_all([snapshot_1, snapshot_2])
    db_session.commit()

    return {
        "company": company,
        "uploads": [upload_1, upload_2],
        "snapshots": [snapshot_1, snapshot_2],
    }
