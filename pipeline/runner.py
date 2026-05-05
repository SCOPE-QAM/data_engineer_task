import json, logging, os, time
from datetime import datetime, timezone
from pathlib import Path
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from api.database import SessionLocal
from api.models import PipelineRun
from pipeline.extractor import extract_file
from pipeline.loader import load_file

logging.basicConfig(level=getattr(logging, os.environ.get("LOG_LEVEL","INFO")),
                    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
log = logging.getLogger(__name__)

DATA_DIR = os.environ.get("DATA_DIR", "/app/data")


@retry(retry=retry_if_exception_type(Exception),
       wait=wait_exponential(multiplier=1, min=2, max=30),
       stop=stop_after_attempt(3), reraise=True)
def _process(filepath: str, run_id: int) -> dict:
    session = SessionLocal()
    try:
        meta, data = extract_file(filepath)
        upload = load_file(session, meta, data, run_id=run_id)
        session.commit()
        if upload is None:
            return {"status": "skipped", "filename": meta.filename}
        return {"status": "success", "filename": meta.filename,
                "upload_id": upload.upload_id, "company": data.company_info.rated_entity,
                "ms": upload.processing_ms}
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def run_pipeline(data_dir: str = None) -> dict:
    data_dir = data_dir or DATA_DIR
    files = sorted(Path(data_dir).glob("*.xlsm"))
    log.info("Found %d files in %s", len(files), data_dir)

    session = SessionLocal()
    run = PipelineRun(started_at=datetime.now(timezone.utc), status="running",
                      files_discovered=len(files))
    session.add(run); session.commit()
    run_id = run.run_id; session.close()

    results, processed, skipped, failed = [], 0, 0, 0
    t0 = time.monotonic()

    for f in files:
        log.info("Processing %s", f.name)
        try:
            r = _process(str(f), run_id)
            results.append(r)
            if r["status"] == "skipped": skipped += 1
            else: processed += 1
        except Exception as exc:
            failed += 1
            results.append({"status": "failed", "filename": f.name, "error": str(exc)})
            log.error("Failed %s: %s", f.name, exc)

    elapsed = int((time.monotonic() - t0) * 1000)
    status = "success" if failed == 0 else ("partial" if processed > 0 else "failed")

    report = {"status": status, "files_discovered": len(files), "files_processed": processed,
              "files_skipped": skipped, "files_failed": failed,
              "duration_ms": elapsed, "per_file": results}

    session = SessionLocal()
    try:
        pr = session.get(PipelineRun, run_id)
        pr.completed_at = datetime.now(timezone.utc)
        pr.status = status
        pr.files_processed = processed; pr.files_skipped = skipped; pr.files_failed = failed
        pr.quality_report = report
        session.commit()
    finally:
        session.close()

    log.info("Pipeline done: processed=%d skipped=%d failed=%d (%dms)",
             processed, skipped, failed, elapsed)
    return report

if __name__ == "__main__":
    import time
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    class XlsmHandler(FileSystemEventHandler):
        def on_created(self, event):
            if event.src_path.endswith(".xlsm"):
                log.info("New file detected: %s", event.src_path)
                time.sleep(1)
                try:
                    session = SessionLocal()
                    run = PipelineRun(
                        started_at=datetime.now(timezone.utc),
                        status="running",
                        files_discovered=1,
                    )
                    session.add(run)
                    session.commit()
                    run_id = run.run_id
                    session.close()

                    result = _process(event.src_path, run_id=run_id)
                    log.info("Result: %s", result)

                    session = SessionLocal()
                    pr = session.get(PipelineRun, run_id)
                    pr.completed_at = datetime.now(timezone.utc)
                    pr.status = result["status"]
                    pr.files_processed = 1 if result["status"] == "success" else 0
                    pr.files_failed = 1 if result["status"] == "failed" else 0
                    pr.quality_report = result
                    session.commit()
                    session.close()

                except Exception as exc:
                    log.error("Failed to process %s: %s", event.src_path, exc, exc_info=True)

    # run pipeline on existing files first
    print(json.dumps(run_pipeline(), indent=2, default=str))

    # then watch for new files
    log.info("Watching %s for new .xlsm files...", DATA_DIR)
    observer = Observer()
    observer.schedule(XlsmHandler(), DATA_DIR, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
