from app.services.transformer import transform
from app.services.validator import validate


def test_transform_maps_master_fields_and_casts_weight():
    """Transform should map master fields and cast the weight value."""
    raw = {
        "rated entity": "TestCo",
        "corporatesector": "Industrial",
        "country of origin": "FR",
        "reporting currency/units": "EUR",
        "industry risk score": "BBB",
        "industry weight": "0.5",
        "accounting principles": "IFRS",
        "end of business year": "December",
    }

    result = transform(raw)

    assert result == {
        "name": "TestCo",
        "sector": "Industrial",
        "country": "FR",
        "currency": "EUR",
        "industry_score": "BBB",
        "industry_weight": 0.5,
        "accounting": "IFRS",
        "year_end": "December",
    }


def test_transform_defaults_missing_weight_to_zero():
    """Transform should default a missing weight to zero."""
    result = transform({"rated entity": "TestCo"})

    assert result["industry_weight"] == 0.0


def test_validate_accepts_valid_payload_without_errors():
    """Validate should accept a complete payload without issues."""
    report = validate(
        {
            "rated entity": "TestCo",
            "corporatesector": "Industrial",
            "industry weight": "0.7",
        }
    )

    assert {k: report[k] for k in ["errors", "warnings", "valid"]} == {
        "errors": [],
        "warnings": [],
        "valid": True,
    }


def test_validate_reports_missing_company_invalid_weight_and_missing_sector():
    """Validate should report missing required and malformed fields."""
    report = validate({"industry weight": "not-a-number"})

    assert report["valid"] is False
    assert "Missing company" in report["errors"]
    assert "Weight not numeric" in report["errors"]
    assert "Missing sector" in report["warnings"]


def test_validate_rejects_weight_outside_expected_range():
    """Validate should reject weights outside the supported range."""
    report = validate(
        {
            "rated entity": "TestCo",
            "corporatesector": "Industrial",
            "industry weight": "1.5",
        }
    )

    assert report["valid"] is False
    assert report["errors"] == ["Invalid weight range"]
