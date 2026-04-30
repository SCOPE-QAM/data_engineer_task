import os
import shutil
from pathlib import Path

from app.models import Company, Snapshot, Upload
from app.pipeline.orchestrator import run_pipeline


def test_pipeline_loads_real_xlsm_file(db_session, tmp_path):
    os.environ["DATABASE_URL"] = str(db_session.bind.url)

    source = Path("data/corporates_A_1.xlsm")
    target = tmp_path / source.name
    shutil.copy2(source, target)

    run_pipeline(folder=str(tmp_path), db=db_session)

    db_session.commit()
    db_session.expire_all()

    company = db_session.query(Company).one()
    upload = db_session.query(Upload).one()
    snapshot = db_session.query(Snapshot).one()

    assert company.name == "Company A"
    assert company.sector == "Personal & Household Goods"
    assert upload.file_name.endswith("corporates_A_1.xlsm")
    assert snapshot.industry_score == "A"
    assert snapshot.industry_weight == 1.0
    assert snapshot.currency == "EUR"
    assert snapshot.is_current is True


def test_pipeline_is_idempotent_for_same_real_file(db_session, tmp_path):
    os.environ["DATABASE_URL"] = str(db_session.bind.url)

    source = Path("data/corporates_A_1.xlsm")
    target = tmp_path / source.name
    shutil.copy2(source, target)

    run_pipeline(folder=str(tmp_path), db=db_session)
    run_pipeline(folder=str(tmp_path), db=db_session)

    db_session.commit()
    db_session.expire_all()

    assert db_session.query(Company).count() == 1
    assert db_session.query(Upload).count() == 1
    assert db_session.query(Snapshot).count() == 1
