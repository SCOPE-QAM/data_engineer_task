from dataclasses import dataclass, field
from typing import Optional
from pipeline.extractor import MasterSheetData

REQUIRED = {
    "rated_entity":    lambda d: d.company_info.rated_entity,
    "corporate_sector":lambda d: d.company_info.corporate_sector,
    "country_of_origin":lambda d: d.reporting_info.country_of_origin,
    "reporting_currency":lambda d: d.reporting_info.reporting_currency,
}

@dataclass
class Issue:
    field_name: str
    rule: str
    is_valid: bool
    severity: str
    message: str
    raw_value: Optional[str] = None

@dataclass
class ValidationReport:
    company_id: Optional[str]
    issues: list[Issue] = field(default_factory=list)

    @property
    def has_errors(self): return any(i.severity == "error" and not i.is_valid for i in self.issues)
    @property
    def error_count(self): return sum(1 for i in self.issues if i.severity == "error" and not i.is_valid)
    @property
    def warning_count(self): return sum(1 for i in self.issues if i.severity == "warning" and not i.is_valid)
    @property
    def validity_rate(self): return round(100 * sum(1 for i in self.issues if i.is_valid) / len(self.issues), 2) if self.issues else 0.0

    def summary(self):
        return {"company_id": self.company_id, "errors": self.error_count,
                "warnings": self.warning_count, "validity_rate": self.validity_rate,
                "has_errors": self.has_errors}


def validate(data: MasterSheetData) -> ValidationReport:
    issues = []
    company_id = data.company_info.rated_entity

    # required fields
    for fname, getter in REQUIRED.items():
        val = getter(data)
        present = bool(val and str(val).strip())
        issues.append(Issue(fname, "required_field", present, "error",
                            f"'{fname}' present" if present else f"'{fname}' missing",
                            str(val) if val else None))

    # industry weight should be numeric and <= 1
    w = data.industry_risk.industry_weight
    if w is not None:
        valid = 0.0 <= w <= 1.0
        issues.append(Issue("industry_weight", "weight_range", valid, "warning",
                            f"weight={w} OK" if valid else f"weight={w} out of [0,1]", str(w)))

    # at least one methodology
    has_method = len(data.rating_methodologies) > 0
    issues.append(Issue("rating_methodologies", "methodology_present", has_method, "warning",
                        "methodologies present" if has_method else "no methodologies found"))

    # scope metrics have values
    has_scope = len(data.scope_metrics) > 0
    issues.append(Issue("scope_metrics", "scope_present", has_scope, "warning",
                        "scope metrics present" if has_scope else "no scope metrics found"))

    # currency 3-letter
    cur = data.reporting_info.reporting_currency
    if cur:
        valid = len(cur.strip()) == 3 and cur.strip().isalpha()
        issues.append(Issue("reporting_currency", "currency_code", valid, "warning",
                            f"currency '{cur}' OK" if valid else f"currency '{cur}' not 3-letter ISO", cur))

    return ValidationReport(company_id=company_id, issues=issues)


def completeness(data: MasterSheetData) -> float:
    present = sum(1 for _, g in REQUIRED.items() if g(data) and str(g(data)).strip())
    return round(100 * present / len(REQUIRED), 2)
