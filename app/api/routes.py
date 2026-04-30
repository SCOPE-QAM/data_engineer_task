from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Company, Snapshot, Upload
from app.schemas import SnapshotSchema

router = APIRouter()


def get_db():
    """Yield a database session for request handlers."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/companies")
def companies(db: Session = Depends(get_db)):
    """Return all companies."""
    return db.query(Company).all()


@router.get("/companies/compare")
def compare(company_ids: str, as_of: str, db: Session = Depends(get_db)):
    """Return point-in-time snapshots for the requested companies."""
    ids = [int(x) for x in company_ids.split(",")]

    result = db.execute(
        text(
            """
            SELECT c.name, f.*
            FROM fact_snapshot f
            JOIN dim_company c ON c.id = f.company_id
            WHERE f.company_id = ANY(:ids)
            AND f.valid_from <= :as_of
            AND (f.valid_to IS NULL OR f.valid_to > :as_of)
            ORDER BY c.name
            """
        ),
        {"ids": ids, "as_of": as_of},
    )

    return [dict(r._mapping) for r in result]


@router.get("/companies/{id}")
def get_company(id: int, db: Session = Depends(get_db)):
    """Return a single company by id."""
    return db.query(Company).filter_by(id=id).first()


@router.get("/companies/{id}/versions")
def versions(id: int, db: Session = Depends(get_db)):
    """Return all snapshots for a company."""
    return db.query(Snapshot).filter_by(company_id=id).all()


@router.get("/companies/{id}/history")
def history(id: int, db: Session = Depends(get_db)):
    """Return a company's snapshots ordered by validity start."""
    return db.query(Snapshot).filter(Snapshot.company_id == id).order_by(Snapshot.valid_from).all()


@router.get("/snapshots/latest", response_model=list[SnapshotSchema])
def latest(db: Session = Depends(get_db)):
    """Return the latest snapshot for each company."""
    return db.query(Snapshot).filter_by(is_current=True).all()


@router.get("/snapshots")
def snapshots(company_id: int = None, db: Session = Depends(get_db)):
    """Return snapshots, optionally filtered by company id."""
    query = db.query(Snapshot)

    if company_id:
        query = query.filter(Snapshot.company_id == company_id)

    return query.all()


@router.get("/snapshots/{id}")
def snapshot(id: int, db: Session = Depends(get_db)):
    """Return a snapshot enriched with upload metadata."""
    result = db.execute(
        text(
            """
        SELECT f.*, u.file_name, u.uploaded_at
        FROM fact_snapshot f
        JOIN dim_upload u ON u.id = f.upload_id
        WHERE f.id = :id
        """
        ),
        {"id": id},
    ).fetchone()

    return dict(result._mapping) if result else None


@router.get("/uploads")
def uploads(db: Session = Depends(get_db)):
    """Return all uploads."""
    return db.query(Upload).all()


@router.get("/uploads/stats")
def upload_stats(db: Session = Depends(get_db)):
    """Return aggregate upload statistics."""
    total = db.query(Upload).count()
    return {"total_uploads": total}


@router.get("/uploads/{upload_id}")
def upload_detail(upload_id: int, db: Session = Depends(get_db)):
    """Return a single upload by id."""
    return db.query(Upload).filter_by(id=upload_id).first()
