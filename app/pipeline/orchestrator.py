import logging
import os
import time

from app.db import SessionLocal
from app.services.extractor import extract_master
from app.services.loader import load
from app.services.transformer import transform
from app.services.validator import validate

logger = logging.getLogger(__name__)


def run_pipeline(folder="data", db=None):
    """Extract, validate, transform, and load `.xlsm` files from a folder."""
    db = db or SessionLocal()
    start = time.time()

    for file in sorted(os.listdir(folder)):
        if not file.endswith(".xlsm"):
            continue

        file_start = time.time()

        path = f"{folder}/{file}"
        raw = extract_master(path)

        report = validate(raw)

        if not report["valid"]:
            logger.error(f"{file} failed validation: {report['errors']}")
            continue

        clean = transform(raw)
        result = load(db, path, clean)

        file_duration = time.time() - file_start
        logger.info(f"{file} | {result} | {file_duration:.2f}s")

    total_duration = time.time() - start
    logger.info(f"Pipeline finished in {total_duration:.2f}s")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_pipeline()
