"""
Tests for pipeline/runner.py.

Covers:
- run_pipeline() with an empty directory (success, zero counts)
- PipelineRun record creation and field population
- Failed file counted correctly (_process mocked to avoid retry delays)
- Report structure
"""
import tempfile
from pathlib import Path
from unittest.mock import patch

from api.models import PipelineRun
from tests.conftest import TestSession


class TestRunPipeline:
    def test_empty_dir_returns_success(self):
        from pipeline.runner import run_pipeline
        with tempfile.TemporaryDirectory() as d:
            with patch("pipeline.runner.SessionLocal", TestSession):
                result = run_pipeline(d)
        assert result["status"] == "success"

    def test_empty_dir_zero_counts(self):
        from pipeline.runner import run_pipeline
        with tempfile.TemporaryDirectory() as d:
            with patch("pipeline.runner.SessionLocal", TestSession):
                result = run_pipeline(d)
        assert result["files_discovered"] == 0
        assert result["files_processed"] == 0
        assert result["files_failed"] == 0

    def test_creates_pipeline_run_record(self, db):
        from pipeline.runner import run_pipeline
        before = db.query(PipelineRun).count()
        with tempfile.TemporaryDirectory() as d:
            with patch("pipeline.runner.SessionLocal", TestSession):
                run_pipeline(d)
        assert db.query(PipelineRun).count() > before

    def test_run_record_has_completed_at(self, db):
        from pipeline.runner import run_pipeline
        with tempfile.TemporaryDirectory() as d:
            with patch("pipeline.runner.SessionLocal", TestSession):
                run_pipeline(d)
        run = db.query(PipelineRun).order_by(PipelineRun.run_id.desc()).first()
        assert run.completed_at is not None

    def test_run_record_status_is_valid(self, db):
        from pipeline.runner import run_pipeline
        with tempfile.TemporaryDirectory() as d:
            with patch("pipeline.runner.SessionLocal", TestSession):
                run_pipeline(d)
        run = db.query(PipelineRun).order_by(PipelineRun.run_id.desc()).first()
        assert run.status in ("success", "partial", "failed")

    def test_failed_file_counted(self):
        from pipeline.runner import run_pipeline
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "bad.xlsm").write_bytes(b"not excel")
            with patch("pipeline.runner.SessionLocal", TestSession), \
                 patch("pipeline.runner._process", side_effect=Exception("corrupt")):
                result = run_pipeline(d)
        assert result["files_discovered"] == 1
        assert result["files_failed"] == 1
        assert result["status"] == "failed"

    def test_report_has_per_file_list(self):
        from pipeline.runner import run_pipeline
        with tempfile.TemporaryDirectory() as d:
            with patch("pipeline.runner.SessionLocal", TestSession):
                result = run_pipeline(d)
        assert isinstance(result.get("per_file"), list)

    def test_report_has_duration_ms(self):
        from pipeline.runner import run_pipeline
        with tempfile.TemporaryDirectory() as d:
            with patch("pipeline.runner.SessionLocal", TestSession):
                result = run_pipeline(d)
        assert "duration_ms" in result
