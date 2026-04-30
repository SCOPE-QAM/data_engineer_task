import hashlib

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Company, Snapshot, Upload


def file_hash(path):
    """Return the MD5 hash for a file."""
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def load(db: Session, path: str, data: dict):
    """Persist an upload, company, and current snapshot when new data arrives."""
    hash_ = file_hash(path)

    existing = db.query(Upload).filter_by(file_hash=hash_).first()
    if existing:
        return "Already processed"

    upload = Upload(file_name=path, file_hash=hash_)
    db.add(upload)
    db.commit()

    company = db.query(Company).filter_by(name=data["name"]).first()
    if not company:
        company = Company(
            name=data["name"],
            sector=data["sector"],
            country=data["country"],
        )
        db.add(company)
        db.commit()

    db.query(Snapshot).filter_by(company_id=company.id, is_current=True).update(
        {"valid_to": func.now(), "is_current": False}
    )

    snapshot = Snapshot(
        company_id=company.id,
        upload_id=upload.id,
        industry_score=data["industry_score"],
        industry_weight=data["industry_weight"],
        currency=data["currency"],
        accounting=data["accounting"],
        year_end=data["year_end"],
    )

    db.add(snapshot)
    db.commit()

    return "Inserted"
