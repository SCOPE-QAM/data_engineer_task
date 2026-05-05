import logging
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.database import check_connection
from api.routers.companies import router as companies_router
from api.routers.views import snapshots, uploads
from api.schemas import HealthResponse

log = logging.getLogger(__name__)

app = FastAPI(
    title="Credit Rating Analytics API",
    description="Corporate credit rating data platform — extracts, stores and exposes rating metadata from .xlsm submissions.",
    version="1.0.0",
    openapi_tags=[
        {"name": "companies", "description": "Company metadata, versions, history, comparisons"},
        {"name": "snapshots", "description": "Point-in-time snapshots"},
        {"name": "uploads",   "description": "File upload audit trail"},
    ]
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])

app.include_router(companies_router)
app.include_router(snapshots)
app.include_router(uploads)

@app.get("/", tags=["health"])
def root():
    return {"service": "Credit Rating Analytics API", "docs": "/docs", "health": "/health"}

@app.get("/health", response_model=HealthResponse, tags=["health"])
def health():
    ok = check_connection()
    return HealthResponse(status="healthy" if ok else "degraded",
                          database="connected" if ok else "unreachable",
                          timestamp=datetime.now(timezone.utc))
