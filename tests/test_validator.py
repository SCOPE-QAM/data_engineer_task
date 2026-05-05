"""
Tests for pipeline/validator.py.

Covers:
- Required field presence (errors)
- Industry weight range (warning)
- Methodology and scope metrics presence (warnings)
- Currency format check (warning)
- completeness() scoring
- ValidationReport properties: has_errors, error_count, warning_count,
  validity_rate, summary()
"""
from pipeline.validator import validate, completeness
from tests.conftest import sample_data


# ── required field errors ─────────────────────────────────────────────────────

class TestRequiredFields:
    def test_valid_data_has_no_errors(self):
        assert validate(sample_data()).error_count == 0

    def test_missing_rated_entity(self):
        d = sample_data(); d.company_info.rated_entity = None
        assert validate(d).has_errors

    def test_missing_reporting_currency(self):
        d = sample_data(); d.reporting_info.reporting_currency = None
        assert validate(d).has_errors

    def test_missing_country_of_origin(self):
        d = sample_data(); d.reporting_info.country_of_origin = None
        assert validate(d).has_errors

    def test_missing_corporate_sector(self):
        d = sample_data(); d.company_info.corporate_sector = None
        assert validate(d).has_errors

    def test_two_missing_fields_counts_two_errors(self):
        d = sample_data()
        d.company_info.rated_entity = None
        d.reporting_info.reporting_currency = None
        assert validate(d).error_count == 2


# ── industry weight ───────────────────────────────────────────────────────────

class TestIndustryWeight:
    def test_weight_over_one_is_invalid(self):
        d = sample_data(); d.industry_risk.industry_weight = 1.5
        issues = [i for i in validate(d).issues if i.field_name == "industry_weight"]
        assert issues and not issues[0].is_valid

    def test_weight_zero_is_valid(self):
        d = sample_data(); d.industry_risk.industry_weight = 0.0
        issues = [i for i in validate(d).issues if i.field_name == "industry_weight"]
        assert issues[0].is_valid

    def test_weight_one_is_valid(self):
        d = sample_data(); d.industry_risk.industry_weight = 1.0
        issues = [i for i in validate(d).issues if i.field_name == "industry_weight"]
        assert issues[0].is_valid

    def test_weight_none_skipped(self):
        d = sample_data(); d.industry_risk.industry_weight = None
        assert not any(i.field_name == "industry_weight" for i in validate(d).issues)


# ── warnings ──────────────────────────────────────────────────────────────────

class TestWarnings:
    def test_no_methodologies_flagged(self):
        d = sample_data(); d.rating_methodologies = []
        assert any(not i.is_valid and i.field_name == "rating_methodologies"
                   for i in validate(d).issues)

    def test_no_scope_metrics_flagged(self):
        d = sample_data(); d.scope_metrics = []
        assert any(not i.is_valid and i.field_name == "scope_metrics"
                   for i in validate(d).issues)

    def test_currency_too_long_flagged(self):
        d = sample_data(); d.reporting_info.reporting_currency = "EURO"
        assert any(not i.is_valid and i.rule == "currency_code" for i in validate(d).issues)

    def test_currency_with_digit_flagged(self):
        d = sample_data(); d.reporting_info.reporting_currency = "EU1"
        assert any(not i.is_valid and i.rule == "currency_code" for i in validate(d).issues)

    def test_valid_currency_not_flagged(self):
        issues = [i for i in validate(sample_data()).issues if i.rule == "currency_code"]
        assert not issues or all(i.is_valid for i in issues)

    def test_weight_warning_increments_count(self):
        d = sample_data(); d.industry_risk.industry_weight = 1.5
        assert validate(d).warning_count >= 1


# ── ValidationReport properties ───────────────────────────────────────────────

class TestValidationReport:
    def test_validity_rate_perfect_data(self):
        assert validate(sample_data()).validity_rate == 100.0

    def test_summary_has_all_keys(self):
        keys = validate(sample_data()).summary().keys()
        assert {"company_id", "errors", "warnings", "validity_rate", "has_errors"} == set(keys)

    def test_summary_company_id(self):
        assert validate(sample_data()).summary()["company_id"] == "TestCo"

    def test_has_errors_false_for_valid_data(self):
        assert not validate(sample_data()).has_errors


# ── completeness ──────────────────────────────────────────────────────────────

class TestCompleteness:
    def test_all_required_fields_present(self):
        assert completeness(sample_data()) == 100.0

    def test_one_field_missing(self):
        d = sample_data(); d.company_info.corporate_sector = None
        assert completeness(d) < 100.0

    def test_all_required_fields_missing(self):
        d = sample_data()
        d.company_info.rated_entity = None
        d.company_info.corporate_sector = None
        d.reporting_info.reporting_currency = None
        d.reporting_info.country_of_origin = None
        assert completeness(d) == 0.0
