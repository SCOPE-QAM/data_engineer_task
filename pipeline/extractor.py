import hashlib, math, os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import pandas as pd
import yaml

_CONFIG_PATH = Path(__file__).parent / "table_config.yml"

def _load_config():
    with open(_CONFIG_PATH) as f:
        return yaml.safe_load(f)

_CFG = _load_config()


@dataclass
class FileMetadata:
    filepath: str
    filename: str
    file_size_bytes: int
    file_hash: str
    discussion_group: Optional[str]
    discussion_version: Optional[str]

@dataclass
class CompanyInfo:
    rated_entity: Optional[str] = None
    corporate_sector: Optional[str] = None

@dataclass
class IndustryRisk:
    industry_risk: Optional[str] = None
    industry_risk_score: Optional[str] = None
    industry_weight: Optional[float] = None
    segmentation_criteria: Optional[str] = None

@dataclass
class ReportingInfo:
    reporting_currency: Optional[str] = None
    country_of_origin: Optional[str] = None
    accounting_principles: Optional[str] = None
    end_of_business_year: Optional[str] = None

@dataclass
class BusinessRiskProfile:
    business_risk_profile: Optional[str] = None
    blended_industry_risk_profile: Optional[str] = None
    competitive_positioning: Optional[str] = None
    market_share: Optional[str] = None
    diversification: Optional[str] = None
    operating_profitability: Optional[str] = None
    sector_specific_factor_1: Optional[str] = None
    sector_specific_factor_2: Optional[str] = None

@dataclass
class FinancialRiskProfile:
    financial_risk_profile: Optional[str] = None
    leverage: Optional[str] = None
    interest_cover: Optional[str] = None
    cash_flow_cover: Optional[str] = None
    liquidity: Optional[str] = None

@dataclass
class ScopeCreditMetric:
    metric: str
    values: dict = field(default_factory=dict)  # {year: value}

@dataclass
class MasterSheetData:
    company_info: CompanyInfo
    rating_methodologies: list[str]
    industry_risk: IndustryRisk
    reporting_info: ReportingInfo
    business_risk: BusinessRiskProfile
    financial_risk: FinancialRiskProfile
    scope_metrics: list[ScopeCreditMetric]


# ── helpers ───────────────────────────────────────────────────────────────────

def _sha256(fp):
    h = hashlib.sha256()
    with open(fp, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""): h.update(chunk)
    return h.hexdigest()

def _parse_filename(name):
    parts = Path(name).stem.split("_")
    return (parts[1].upper() if len(parts) > 1 else None,
            parts[2]         if len(parts) > 2 else None)

def _clean(v):
    s = str(v).strip() if v is not None else ""
    return None if s in ("", "nan", "NaN") else s

def _float(v):
    try:
        f = float(v); return None if math.isnan(f) else f
    except (TypeError, ValueError): return None

def _year(v):
    if v is None: return None
    if isinstance(v, int): return str(v)
    if isinstance(v, float): return None if math.isnan(v) else str(int(v))
    s = str(v).strip()
    return None if s in ("", "nan") else s

def _kv(df, r0, r1):
    rows = df.iloc[r0:r1, [1, 2]]
    return {_clean(r[1]): r[2] for _, r in rows.iterrows() if _clean(r[1])}


# ── table extractors ──────────────────────────────────────────────────────────

def _company_info(df):
    t = _CFG["tables"]["company_info"]
    kv = _kv(df, *t["rows"])
    return CompanyInfo(
        rated_entity=_clean(kv.get(t["fields"]["rated_entity"])),
        corporate_sector=_clean(kv.get(t["fields"]["corporate_sector"])),
    )

def _methodologies(df):
    t = _CFG["tables"]["rating_methodologies"]
    return [_clean(v) for v in df.iloc[t["row"], t["start_col"]:] if _clean(v)]

def _industry_risk(df):
    t = _CFG["tables"]["industry_risk"]
    kv = _kv(df, *t["rows"])
    f = t["fields"]
    return IndustryRisk(
        industry_risk=_clean(kv.get(f["industry_risk"])),
        industry_risk_score=_clean(kv.get(f["industry_risk_score"])),
        industry_weight=_float(kv.get(f["industry_weight"])),
        segmentation_criteria=_clean(kv.get(f["segmentation_criteria"])),
    )

def _reporting_info(df):
    t = _CFG["tables"]["reporting_info"]
    kv = _kv(df, *t["rows"])
    f = t["fields"]
    return ReportingInfo(
        reporting_currency=_clean(kv.get(f["reporting_currency"])),
        country_of_origin=_clean(kv.get(f["country_of_origin"])),
        accounting_principles=_clean(kv.get(f["accounting_principles"])),
        end_of_business_year=_clean(kv.get(f["end_of_business_year"])),
    )

def _business_risk(df):
    t = _CFG["tables"]["business_risk"]
    kv = _kv(df, *t["rows"])
    f = t["fields"]
    return BusinessRiskProfile(
        business_risk_profile=_clean(kv.get(f["business_risk_profile"])),
        blended_industry_risk_profile=_clean(kv.get(f["blended_industry_risk_profile"])),
        competitive_positioning=_clean(kv.get(f["competitive_positioning"])),
        market_share=_clean(kv.get(f["market_share"])),
        diversification=_clean(kv.get(f["diversification"])),
        operating_profitability=_clean(kv.get(f["operating_profitability"])),
        sector_specific_factor_1=_clean(kv.get(f["sector_specific_factor_1"])),
        sector_specific_factor_2=_clean(kv.get(f["sector_specific_factor_2"])),
    )

def _financial_risk(df):
    t = _CFG["tables"]["financial_risk"]
    kv = _kv(df, *t["rows"])
    f = t["fields"]
    return FinancialRiskProfile(
        financial_risk_profile=_clean(kv.get(f["financial_risk_profile"])),
        leverage=_clean(kv.get(f["leverage"])),
        interest_cover=_clean(kv.get(f["interest_cover"])),
        cash_flow_cover=_clean(kv.get(f["cash_flow_cover"])),
        liquidity=_clean(kv.get(f["liquidity"])),
    )

def _scope_metrics(df):
    t = _CFG["tables"]["scope_metrics"]
    start_col = t["start_col"]
    years = [_year(v) for v in df.iloc[t["year_row"], start_col:] if _year(v)]
    metrics = []
    r0, r1 = t["data_rows"]
    for i in range(r0, r1):
        name = _clean(df.iloc[i, 1])
        if not name: continue
        values = {y: v for y, col in zip(years, range(start_col, start_col + len(years)))
                  if (v := _float(df.iloc[i, col])) is not None}
        metrics.append(ScopeCreditMetric(metric=name, values=values))
    return metrics


# ── main ──────────────────────────────────────────────────────────────────────

def extract_file(filepath: str) -> tuple[FileMetadata, MasterSheetData]:
    filename = os.path.basename(filepath)
    group, version = _parse_filename(filename)
    meta = FileMetadata(
        filepath=filepath, filename=filename,
        file_size_bytes=os.path.getsize(filepath),
        file_hash=_sha256(filepath),
        discussion_group=group, discussion_version=version,
    )
    df = pd.read_excel(filepath, sheet_name=_CFG["sheet"], header=None, engine="openpyxl")
    data = MasterSheetData(
        company_info=_company_info(df),
        rating_methodologies=_methodologies(df),
        industry_risk=_industry_risk(df),
        reporting_info=_reporting_info(df),
        business_risk=_business_risk(df),
        financial_risk=_financial_risk(df),
        scope_metrics=_scope_metrics(df),
    )
    return meta, data
