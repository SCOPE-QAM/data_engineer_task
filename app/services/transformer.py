def transform(data: dict):
    """Map raw extracted fields into the normalized snapshot payload."""
    return {
        "name": data.get("rated entity"),
        "sector": data.get("corporatesector"),
        "country": data.get("country of origin"),
        "currency": data.get("reporting currency/units"),
        "industry_score": data.get("industry risk score"),
        "industry_weight": float(data.get("industry weight", 0)),
        "accounting": data.get("accounting principles"),
        "year_end": data.get("end of business year"),
    }
