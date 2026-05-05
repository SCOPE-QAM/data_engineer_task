"""
Tests for pipeline/extractor.py and pipeline/table_config.yml.

Covers:
- Helper functions: _clean, _float, _year, _parse_filename, _kv
- Table extractor functions: _company_info, _methodologies, _industry_risk, etc.
- table_config.yml structure and values
"""
from pipeline.extractor import (
    _clean, _float, _year, _parse_filename, _kv,
    _company_info, _methodologies, _industry_risk, _reporting_info,
    _business_risk, _financial_risk, _scope_metrics,
)
from tests.conftest import make_df


# ── helper functions ──────────────────────────────────────────────────────────

class TestClean:
    def test_none_returns_none(self):         assert _clean(None) is None
    def test_nan_string_returns_none(self):   assert _clean("nan") is None
    def test_NaN_string_returns_none(self):   assert _clean("NaN") is None
    def test_whitespace_returns_none(self):   assert _clean("   ") is None
    def test_strips_surrounding_spaces(self): assert _clean("  hello  ") == "hello"
    def test_valid_value_unchanged(self):     assert _clean("value") == "value"


class TestFloat:
    def test_numeric_string(self):    assert _float("3.5") == 3.5
    def test_integer_string(self):    assert _float("42") == 42.0
    def test_zero(self):              assert _float(0.0) == 0.0
    def test_nan_float(self):         assert _float(float("nan")) is None
    def test_invalid_string(self):    assert _float("abc") is None
    def test_none(self):              assert _float(None) is None


class TestYear:
    def test_integer(self):           assert _year(2020) == "2020"
    def test_float(self):             assert _year(2020.0) == "2020"
    def test_forecast_string(self):   assert _year("2025E") == "2025E"
    def test_nan_float(self):         assert _year(float("nan")) is None
    def test_none(self):              assert _year(None) is None
    def test_empty_string(self):      assert _year("") is None
    def test_nan_string(self):        assert _year("nan") is None


class TestParseFilename:
    def test_group_a_version_1(self):  assert _parse_filename("corporates_A_1.xlsm") == ("A", "1")
    def test_group_b_version_2(self):  assert _parse_filename("corporates_B_2.xlsm") == ("B", "2")
    def test_no_underscore_parts(self):assert _parse_filename("file.xlsm") == (None, None)
    def test_one_part_only(self):      assert _parse_filename("corporates.xlsm") == (None, None)


class TestKv:
    def test_reads_label_and_value(self):
        result = _kv(make_df(), 1, 3)
        assert result["Rated entity"] == "ACME Corp"
        assert result["CorporateSector"] == "Industrials"

    def test_empty_range_returns_empty_dict(self):
        assert _kv(make_df(), 0, 1) == {}


# ── table extractor functions ─────────────────────────────────────────────────

class TestCompanyInfo:
    def test_rated_entity(self):     assert _company_info(make_df()).rated_entity == "ACME Corp"
    def test_corporate_sector(self): assert _company_info(make_df()).corporate_sector == "Industrials"


class TestMethodologies:
    def test_value_present(self):
        assert "Corp Methodology" in _methodologies(make_df())

    def test_none_cells_skipped(self):
        df = make_df()
        df.iloc[4, 3] = None
        assert None not in _methodologies(df)


class TestIndustryRisk:
    def test_industry_risk(self):         assert _industry_risk(make_df()).industry_risk == "Manufacturing"
    def test_industry_risk_score(self):   assert _industry_risk(make_df()).industry_risk_score == "A"
    def test_industry_weight(self):       assert _industry_risk(make_df()).industry_weight == 0.8
    def test_segmentation_criteria(self): assert _industry_risk(make_df()).segmentation_criteria == "EBITDA"


class TestReportingInfo:
    def test_reporting_currency(self):    assert _reporting_info(make_df()).reporting_currency == "EUR"
    def test_country_of_origin(self):     assert _reporting_info(make_df()).country_of_origin == "Germany"
    def test_accounting_principles(self): assert _reporting_info(make_df()).accounting_principles == "IFRS"
    def test_end_of_business_year(self):  assert _reporting_info(make_df()).end_of_business_year == "December"


class TestBusinessRisk:
    def test_business_risk_profile(self):           assert _business_risk(make_df()).business_risk_profile == "B+"
    def test_blended_industry_risk_profile(self):   assert _business_risk(make_df()).blended_industry_risk_profile == "B"
    def test_competitive_positioning(self):         assert _business_risk(make_df()).competitive_positioning == "Strong"
    def test_market_share(self):                    assert _business_risk(make_df()).market_share == "High"
    def test_diversification(self):                 assert _business_risk(make_df()).diversification == "Medium"
    def test_operating_profitability(self):         assert _business_risk(make_df()).operating_profitability == "Good"
    def test_sector_specific_factor_1(self):        assert _business_risk(make_df()).sector_specific_factor_1 == "Factor1"
    def test_sector_specific_factor_2(self):        assert _business_risk(make_df()).sector_specific_factor_2 == "Factor2"


class TestFinancialRisk:
    def test_financial_risk_profile(self): assert _financial_risk(make_df()).financial_risk_profile == "C"
    def test_leverage(self):               assert _financial_risk(make_df()).leverage == "Medium"
    def test_interest_cover(self):         assert _financial_risk(make_df()).interest_cover == "Good"
    def test_cash_flow_cover(self):        assert _financial_risk(make_df()).cash_flow_cover == "Strong"
    def test_liquidity(self):              assert _financial_risk(make_df()).liquidity == "Adequate"


class TestScopeMetrics:
    def test_metric_count(self):
        assert len(_scope_metrics(make_df())) == 2

    def test_ebitda_values(self):
        m = next(x for x in _scope_metrics(make_df()) if x.metric == "EBITDA cover")
        assert m.values == {"2023": 4.5, "2024": 5.1, "2025E": 5.8}

    def test_forecast_year_included(self):
        m = next(x for x in _scope_metrics(make_df()) if x.metric == "EBITDA cover")
        assert "2025E" in m.values

    def test_none_value_excluded(self):
        # Net debt/EBITDA has no 2025E value in the test DataFrame
        m = next(x for x in _scope_metrics(make_df()) if x.metric == "Net debt/EBITDA")
        assert "2025E" not in m.values


# ── table config ──────────────────────────────────────────────────────────────

class TestTableConfig:
    def test_config_loads(self):
        from pipeline.extractor import _CFG
        assert _CFG is not None

    def test_sheet_name(self):
        from pipeline.extractor import _CFG
        assert _CFG["sheet"] == "MASTER"

    def test_all_tables_present(self):
        from pipeline.extractor import _CFG
        expected = {"company_info", "rating_methodologies", "industry_risk",
                    "reporting_info", "business_risk", "financial_risk", "scope_metrics"}
        assert expected == set(_CFG["tables"].keys())

    def test_company_info_row_bounds(self):
        from pipeline.extractor import _CFG
        t = _CFG["tables"]["company_info"]
        assert t["rows"] == [1, 3]
        assert "rated_entity" in t["fields"]
        assert "corporate_sector" in t["fields"]

    def test_scope_metrics_bounds(self):
        from pipeline.extractor import _CFG
        t = _CFG["tables"]["scope_metrics"]
        assert t["year_row"] == 34
        assert len(t["data_rows"]) == 2
        assert t["start_col"] == 2

    def test_rating_methodologies_keys(self):
        from pipeline.extractor import _CFG
        t = _CFG["tables"]["rating_methodologies"]
        assert "row" in t and "start_col" in t

    def test_all_kv_tables_have_rows_and_fields(self):
        from pipeline.extractor import _CFG
        for name in ("company_info", "industry_risk", "reporting_info",
                     "business_risk", "financial_risk"):
            t = _CFG["tables"][name]
            assert "rows" in t, f"{name} missing 'rows'"
            assert "fields" in t, f"{name} missing 'fields'"
