def validate(data: dict):
    """Validate the raw extracted payload and return an issue report."""
    errors = []
    warnings = []

    if not data.get("rated entity"):
        errors.append("Missing company")

    weight = data.get("industry weight")
    if weight:
        try:
            w = float(weight)
            if not (0 <= w <= 1):
                errors.append("Invalid weight range")
        except Exception:
            errors.append("Weight not numeric")

    if not data.get("corporatesector"):
        warnings.append("Missing sector")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "fields_checked": len(data),
            "fields_present": list(data.keys()),
        },
    }
