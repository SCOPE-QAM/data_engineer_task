def test_companies_endpoints_return_seeded_company_and_versions(client, seeded_data):
    """Company endpoints should expose seeded company and snapshot history."""
    company = seeded_data["company"]

    companies_response = client.get("/companies")
    detail_response = client.get(f"/companies/{company.id}")
    versions_response = client.get(f"/companies/{company.id}/versions")
    history_response = client.get(f"/companies/{company.id}/history")

    assert companies_response.status_code == 200
    assert companies_response.json()[0]["name"] == "Alpha Corp"

    assert detail_response.status_code == 200
    assert detail_response.json()["sector"] == "Utilities"

    assert versions_response.status_code == 200
    assert len(versions_response.json()) == 2

    history_scores = [item["industry_score"] for item in history_response.json()]
    assert history_scores == ["A", "BBB"]


def test_snapshot_endpoints_return_current_and_detail_views(client, seeded_data):
    """Snapshot endpoints should return current and detailed snapshot views."""
    current_snapshot = seeded_data["snapshots"][1]

    latest_response = client.get("/snapshots/latest")
    filtered_response = client.get(f"/snapshots?company_id={current_snapshot.company_id}")
    detail_response = client.get(f"/snapshots/{current_snapshot.id}")

    assert latest_response.status_code == 200
    assert latest_response.json() == [
        {
            "id": current_snapshot.id,
            "company_id": current_snapshot.company_id,
            "industry_score": "BBB",
        }
    ]

    assert filtered_response.status_code == 200
    assert len(filtered_response.json()) == 2

    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["upload_id"] == seeded_data["uploads"][1].id
    assert detail["file_name"] == "alpha_v2.xlsm"


def test_upload_endpoints_return_list_stats_and_detail(client, seeded_data):
    """Upload endpoints should return list, stats, and detail payloads."""
    upload = seeded_data["uploads"][0]

    uploads_response = client.get("/uploads")
    stats_response = client.get("/uploads/stats")
    detail_response = client.get(f"/uploads/{upload.id}")

    assert uploads_response.status_code == 200
    assert len(uploads_response.json()) == 2

    assert stats_response.status_code == 200
    assert stats_response.json() == {"total_uploads": 2}

    assert detail_response.status_code == 200
    assert detail_response.json()["file_name"] == "alpha_v1.xlsm"
