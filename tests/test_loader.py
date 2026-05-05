"""
Tests for pipeline/loader.py.

Covers:
- _company_id(): slug generation
- _date_key(): date → int key
- is_processed(): deduplication check
- _upsert_dim(): SCD Type 2 insert / no-change / version bump
- load_file(): success, skip, force, scope timeseries, validation results,
               ProcessedFile tracking, forecast flag, error path
"""
import uuid
from datetime import datetime, timezone

import pytest

from api.models import (FactCompanySnapshot, FactScopeTimeseries,
                        ValidationResult, ProcessedFile)
from pipeline.loader import is_processed, load_file, _company_id, _date_key, _upsert_dim
from tests.conftest import sample_data, sample_meta


# ── helper: _company_id ───────────────────────────────────────────────────────

class TestCompanyId:
    def test_basic_name(self):           assert _company_id("ACME Corp") == "acme_corp"
    def test_already_lowercase(self):    assert _company_id("testco") == "testco"
    def test_special_chars_replaced(self):
        assert _company_id("ABC & DEF (Ltd)") == "abc_def_ltd"
    def test_no_leading_trailing_underscores(self):
        result = _company_id("  Foo  ")
        assert not result.startswith("_") and not result.endswith("_")


# ── helper: _date_key ─────────────────────────────────────────────────────────

class TestDateKey:
    def test_mid_year(self):
        assert _date_key(datetime(2024, 3, 15, tzinfo=timezone.utc)) == 20240315

    def test_jan_first(self):
        assert _date_key(datetime(2023, 1, 1, tzinfo=timezone.utc)) == 20230101


# ── is_processed ─────────────────────────────────────────────────────────────

class TestIsProcessed:
    def test_returns_false_when_absent(self, db):
        assert not is_processed(db, "never_seen.xlsm", "abc123")

    def test_returns_true_when_present(self, db):
        pf = ProcessedFile(filename=f"seen_{uuid.uuid4().hex}.xlsm", file_hash="cafebabe")
        db.add(pf); db.flush()
        assert is_processed(db, pf.filename, "cafebabe")

    def test_returns_false_on_hash_mismatch(self, db):
        pf = ProcessedFile(filename=f"seen_{uuid.uuid4().hex}.xlsm", file_hash="aaa")
        db.add(pf); db.flush()
        assert not is_processed(db, pf.filename, "bbb")


# ── _upsert_dim ───────────────────────────────────────────────────────────────

class TestUpsertDim:
    def test_new_company_created(self, db):
        data = sample_data()
        data.company_info.rated_entity = f"NewCo_{uuid.uuid4().hex[:6]}"
        dim = _upsert_dim(db, sample_meta(), data)
        assert dim.is_current and dim.version == 1

    def test_unchanged_company_returns_same_record(self, db):
        data = sample_data()
        data.company_info.rated_entity = f"StableCo_{uuid.uuid4().hex[:6]}"
        meta = sample_meta()
        dim1 = _upsert_dim(db, meta, data); db.flush()
        dim2 = _upsert_dim(db, meta, data)
        assert dim1.company_key == dim2.company_key

    def test_sector_change_creates_version_2(self, db):
        data = sample_data()
        data.company_info.rated_entity = f"ChangeCo_{uuid.uuid4().hex[:6]}"
        meta = sample_meta()
        dim1 = _upsert_dim(db, meta, data); db.flush()
        data.company_info.corporate_sector = "NewSector"
        dim2 = _upsert_dim(db, meta, data); db.flush()
        assert dim2.version == 2 and dim2.is_current
        db.refresh(dim1)
        assert not dim1.is_current


# ── load_file ────────────────────────────────────────────────────────────────

class TestLoadFile:
    def test_success_returns_upload(self, db):
        upload = load_file(db, sample_meta(), sample_data())
        db.commit()
        assert upload is not None and upload.processing_status == "success"

    def test_rows_extracted_is_one(self, db):
        upload = load_file(db, sample_meta(), sample_data())
        db.commit()
        assert upload.rows_extracted == 1

    def test_skip_when_already_processed(self, db):
        meta = sample_meta()
        db.add(ProcessedFile(filename=meta.filename, file_hash=meta.file_hash))
        db.flush()
        assert load_file(db, meta, sample_data()) is None

    def test_force_bypasses_dedup(self, db):
        meta = sample_meta()
        db.add(ProcessedFile(filename=meta.filename, file_hash=meta.file_hash))
        db.flush()
        upload = load_file(db, meta, sample_data(), force=True)
        db.commit()
        assert upload is not None

    def test_scope_timeseries_row_count(self, db):
        upload = load_file(db, sample_meta(), sample_data())
        db.commit()
        rows = db.query(FactScopeTimeseries).filter_by(upload_id=upload.upload_id).all()
        assert len(rows) == 3  # 2023, 2024, 2025E

    def test_forecast_year_flagged(self, db):
        upload = load_file(db, sample_meta(), sample_data())
        db.commit()
        fc = db.query(FactScopeTimeseries).filter_by(
            upload_id=upload.upload_id, year="2025E").first()
        assert fc is not None and fc.is_forecast

    def test_non_forecast_year_not_flagged(self, db):
        upload = load_file(db, sample_meta(), sample_data())
        db.commit()
        row = db.query(FactScopeTimeseries).filter_by(
            upload_id=upload.upload_id, year="2024").first()
        assert row is not None and not row.is_forecast

    def test_scope_metric_value_stored(self, db):
        upload = load_file(db, sample_meta(), sample_data())
        db.commit()
        row = db.query(FactScopeTimeseries).filter_by(
            upload_id=upload.upload_id, year="2023").first()
        assert float(row.value) == 4.5

    def test_validation_results_created(self, db):
        upload = load_file(db, sample_meta(), sample_data())
        db.commit()
        rows = db.query(ValidationResult).filter_by(upload_id=upload.upload_id).all()
        assert len(rows) > 0

    def test_processed_file_marked(self, db):
        meta = sample_meta()
        load_file(db, meta, sample_data())
        db.commit()
        assert is_processed(db, meta.filename, meta.file_hash)

    def test_snapshot_is_latest(self, db):
        upload = load_file(db, sample_meta(), sample_data())
        db.commit()
        snap = db.query(FactCompanySnapshot).filter_by(upload_id=upload.upload_id).first()
        assert snap is not None and snap.is_latest

    def test_raises_on_corrupt_data(self, db):
        bad = sample_data()
        bad.company_info = None  # AttributeError in validate()
        with pytest.raises(Exception):
            load_file(db, sample_meta(), bad)
