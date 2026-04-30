from pathlib import Path

from app.models import Company, Snapshot, Upload
from app.pipeline.orchestrator import run_pipeline
from app.services.loader import load


def test_load_inserts_company_upload_and_snapshot(db_session, tmp_path):
    """Loading a new file should create company, upload, and snapshot rows."""
    file_path = tmp_path / "alpha_v1.xlsm"
    file_path.write_bytes(b"alpha-v1")

    result = load(
        db_session,
        str(file_path),
        {
            "name": "Alpha Corp",
            "sector": "Utilities",
            "country": "DE",
            "currency": "EUR",
            "industry_score": "A",
            "industry_weight": 0.4,
            "accounting": "IFRS",
            "year_end": "December",
        },
    )

    assert result == "Inserted"
    assert db_session.query(Company).count() == 1
    assert db_session.query(Upload).count() == 1
    snapshot = db_session.query(Snapshot).one()
    assert snapshot.is_current is True
    assert snapshot.industry_score == "A"


def test_load_skips_duplicate_file_hash(db_session, tmp_path):
    """Loading the same file contents twice should be idempotent."""
    file_path = tmp_path / "alpha_v1.xlsm"
    file_path.write_bytes(b"same-content")

    payload = {
        "name": "Alpha Corp",
        "sector": "Utilities",
        "country": "DE",
        "currency": "EUR",
        "industry_score": "A",
        "industry_weight": 0.4,
        "accounting": "IFRS",
        "year_end": "December",
    }

    assert load(db_session, str(file_path), payload) == "Inserted"
    assert load(db_session, str(file_path), payload) == "Already processed"
    assert db_session.query(Upload).count() == 1
    assert db_session.query(Snapshot).count() == 1


def test_load_rolls_previous_snapshot_when_new_version_arrives(db_session, tmp_path):
    """A new version should retire the previous current snapshot."""
    first_file = tmp_path / "alpha_v1.xlsm"
    second_file = tmp_path / "alpha_v2.xlsm"
    first_file.write_bytes(b"alpha-v1")
    second_file.write_bytes(b"alpha-v2")

    base_payload = {
        "name": "Alpha Corp",
        "sector": "Utilities",
        "country": "DE",
        "currency": "EUR",
        "accounting": "IFRS",
        "year_end": "December",
    }

    load(
        db_session,
        str(first_file),
        {**base_payload, "industry_score": "A", "industry_weight": 0.4},
    )
    load(
        db_session,
        str(second_file),
        {**base_payload, "industry_score": "BBB", "industry_weight": 0.6},
    )

    snapshots = db_session.query(Snapshot).order_by(Snapshot.id).all()
    assert len(snapshots) == 2
    assert snapshots[0].is_current is False
    assert snapshots[0].valid_to is not None
    assert snapshots[1].is_current is True
    assert snapshots[1].industry_score == "BBB"


def test_pipeline_processes_only_valid_xlsm_files_in_sorted_order(monkeypatch, tmp_path):
    """The pipeline should skip invalid files and process `.xlsm` files in order."""
    for name in ["b_file.xlsm", "a_file.xlsm", "notes.txt"]:
        (tmp_path / name).write_text("placeholder")

    extracted = []
    loaded = []

    def fake_extract(path):
        """Capture extraction order during the pipeline run."""
        extracted.append(Path(path).name)
        return {"rated entity": Path(path).stem}

    def fake_validate(raw):
        """Reject one file to exercise the validation branch."""
        return {"valid": raw["rated entity"] != "b_file", "errors": [], "warnings": []}

    def fake_transform(raw):
        """Return a minimal normalized payload for the loader stub."""
        return {"name": raw["rated entity"]}

    def fake_load(db, path, clean):
        """Capture load order without touching the database."""
        loaded.append((Path(path).name, clean["name"]))
        return "Inserted"

    monkeypatch.setattr("app.pipeline.orchestrator.extract_master", fake_extract)
    monkeypatch.setattr("app.pipeline.orchestrator.validate", fake_validate)
    monkeypatch.setattr("app.pipeline.orchestrator.transform", fake_transform)
    monkeypatch.setattr("app.pipeline.orchestrator.load", fake_load)

    run_pipeline(folder=str(tmp_path))

    assert extracted == ["a_file.xlsm", "b_file.xlsm"]
    assert loaded == [("a_file.xlsm", "a_file")]
