"""
Tests for the FastAPI layer (api/).

Covers:
- GET /  and  GET /health
- GET /companies  (list, filters, get, versions, history, compare, scope)
- GET /snapshots  (list, latest, get, filters)
- GET /uploads    (list, stats, details, validations, file download, filters)
"""
import uuid
from tests.conftest import seed, seed_scope


# ── health ────────────────────────────────────────────────────────────────────

class TestHealth:
    def test_root_200(self, client):
        assert client.get("/").status_code == 200

    def test_root_has_service_key(self, client):
        assert "service" in client.get("/").json()

    def test_health_200(self, client):
        assert client.get("/health").status_code == 200

    def test_health_has_status_key(self, client):
        assert "status" in client.get("/health").json()


# ── companies ─────────────────────────────────────────────────────────────────

class TestCompanyList:
    def test_returns_200(self, client, db):
        seed(db, f"List_{uuid.uuid4().hex[:6]}")
        assert client.get("/companies").status_code == 200

    def test_returns_list(self, client):
        assert isinstance(client.get("/companies").json(), list)

    def test_filter_by_sector(self, client):
        assert client.get("/companies?sector=Tech").status_code == 200

    def test_filter_by_country(self, client):
        assert client.get("/companies?country=Germany").status_code == 200

    def test_filter_by_currency(self, client):
        assert client.get("/companies?currency=EUR").status_code == 200


class TestCompanyGet:
    def test_returns_200(self, client, db):
        s = seed(db, f"Get_{uuid.uuid4().hex[:6]}")
        assert client.get(f"/companies/{s.company_id}").status_code == 200

    def test_response_contains_fields(self, client, db):
        s = seed(db, f"Fields_{uuid.uuid4().hex[:6]}")
        data = client.get(f"/companies/{s.company_id}").json()
        assert data["company_id"] == s.company_id
        assert data["rated_entity"] == s.rated_entity

    def test_unknown_company_404(self, client):
        assert client.get("/companies/totally_nonexistent_xyz").status_code == 404


class TestCompanyVersions:
    def test_returns_200(self, client, db):
        s = seed(db, f"Ver_{uuid.uuid4().hex[:6]}")
        assert client.get(f"/companies/{s.company_id}/versions").status_code == 200

    def test_returns_list(self, client, db):
        s = seed(db, f"VerList_{uuid.uuid4().hex[:6]}")
        assert isinstance(client.get(f"/companies/{s.company_id}/versions").json(), list)

    def test_unknown_company_404(self, client):
        assert client.get("/companies/no_such_co_xyz/versions").status_code == 404


class TestCompanyHistory:
    def test_returns_200(self, client, db):
        s = seed(db, f"His_{uuid.uuid4().hex[:6]}")
        assert client.get(f"/companies/{s.company_id}/history").status_code == 200

    def test_unknown_company_404(self, client):
        assert client.get("/companies/no_history_xyz/history").status_code == 404


class TestCompanyCompare:
    def test_returns_200(self, client, db):
        s1 = seed(db, f"CmpA_{uuid.uuid4().hex[:6]}")
        s2 = seed(db, f"CmpB_{uuid.uuid4().hex[:6]}")
        r = client.get(f"/companies/compare?company_ids={s1.company_id},{s2.company_id}")
        assert r.status_code == 200

    def test_empty_company_ids_returns_400(self, client):
        assert client.get("/companies/compare?company_ids=").status_code == 400

    def test_unknown_ids_return_empty_list(self, client):
        r = client.get("/companies/compare?company_ids=no_such_1,no_such_2")
        assert r.status_code == 200 and r.json() == []


class TestCompanyScope:
    def test_no_scope_data_404(self, client):
        assert client.get("/companies/no_scope_ever_xyz/scope").status_code == 404

    def test_returns_200_with_data(self, client, db):
        snap = seed_scope(db, f"ScopeApi_{uuid.uuid4().hex[:6]}")
        assert client.get(f"/companies/{snap.company_id}/scope").status_code == 200

    def test_response_shape(self, client, db):
        snap = seed_scope(db, f"ScopeShape_{uuid.uuid4().hex[:6]}")
        data = client.get(f"/companies/{snap.company_id}/scope").json()
        assert len(data) > 0
        assert {"metric", "year", "value", "is_forecast"} <= set(data[0].keys())

    def test_metric_filter(self, client, db):
        snap = seed_scope(db, f"ScopeFilt_{uuid.uuid4().hex[:6]}")
        r = client.get(f"/companies/{snap.company_id}/scope?metric=EBITDA")
        assert r.status_code == 200


# ── snapshots ─────────────────────────────────────────────────────────────────

class TestSnapshotList:
    def test_returns_200(self, client):
        assert client.get("/snapshots").status_code == 200

    def test_returns_list(self, client):
        assert isinstance(client.get("/snapshots").json(), list)

    def test_filter_by_company_id(self, client, db):
        s = seed(db, f"SnapFilt_{uuid.uuid4().hex[:6]}")
        r = client.get(f"/snapshots?company_id={s.company_id}")
        assert r.status_code == 200
        assert all(row["company_id"] == s.company_id for row in r.json())

    def test_filter_by_sector(self, client):
        assert client.get("/snapshots?sector=Tech").status_code == 200

    def test_filter_by_currency(self, client):
        assert client.get("/snapshots?currency=EUR").status_code == 200

    def test_filter_by_country(self, client):
        assert client.get("/snapshots?country=Germany").status_code == 200


class TestSnapshotLatest:
    def test_returns_200(self, client):
        assert client.get("/snapshots/latest").status_code == 200

    def test_all_rows_are_latest(self, client, db):
        seed(db, f"LatSnap_{uuid.uuid4().hex[:6]}")
        data = client.get("/snapshots/latest").json()
        assert all(row["is_latest"] for row in data)


class TestSnapshotGet:
    def test_returns_200(self, client, db):
        s = seed(db, f"Snap_{uuid.uuid4().hex[:6]}")
        assert client.get(f"/snapshots/{s.snapshot_id}").status_code == 200

    def test_unknown_snapshot_404(self, client):
        assert client.get("/snapshots/999999").status_code == 404


# ── uploads ───────────────────────────────────────────────────────────────────

class TestUploadList:
    def test_returns_200(self, client):
        assert client.get("/uploads").status_code == 200

    def test_returns_list(self, client):
        assert isinstance(client.get("/uploads").json(), list)

    def test_filter_by_status(self, client):
        assert client.get("/uploads?status=success").status_code == 200


class TestUploadStats:
    def test_returns_200(self, client):
        assert client.get("/uploads/stats").status_code == 200

    def test_has_all_expected_keys(self, client):
        data = client.get("/uploads/stats").json()
        for key in ("total_uploads", "successful", "failed",
                    "total_companies", "total_snapshots"):
            assert key in data


class TestUploadDetails:
    def test_returns_200(self, client, db):
        s = seed(db, f"Det_{uuid.uuid4().hex[:6]}")
        assert client.get(f"/uploads/{s.upload_id}/details").status_code == 200

    def test_response_contains_upload_id(self, client, db):
        s = seed(db, f"DetId_{uuid.uuid4().hex[:6]}")
        data = client.get(f"/uploads/{s.upload_id}/details").json()
        assert data["upload_id"] == s.upload_id

    def test_unknown_upload_404(self, client):
        assert client.get("/uploads/999999/details").status_code == 404


class TestUploadValidations:
    def test_returns_200(self, client, db):
        s = seed(db, f"Val_{uuid.uuid4().hex[:6]}")
        assert client.get(f"/uploads/{s.upload_id}/validations").status_code == 200

    def test_returns_list(self, client, db):
        s = seed(db, f"ValList_{uuid.uuid4().hex[:6]}")
        assert isinstance(client.get(f"/uploads/{s.upload_id}/validations").json(), list)


class TestUploadFileDownload:
    def test_file_not_on_disk_returns_404(self, client, db):
        s = seed(db, f"Dl_{uuid.uuid4().hex[:6]}")
        assert client.get(f"/uploads/{s.upload_id}/file").status_code == 404
