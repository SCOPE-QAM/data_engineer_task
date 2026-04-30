from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize application resources during startup."""
    del app
    init_db()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(router)
