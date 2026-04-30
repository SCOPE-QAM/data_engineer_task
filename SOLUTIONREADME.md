# Solution README

## Summary
This project implements a production-oriented ETL pipeline and API for corporate credit rating workbooks.

The solution:
- extracts key-value data from the `MASTER` sheet of `.xlsm` files
- validates raw fields before loading
- transforms workbook fields into a normalized warehouse shape
- stores upload history and temporal snapshots in PostgreSQL
- exposes the data through FastAPI endpoints for current, historical, and upload views

The solution satisfies all core functional requirements: historical tracking, point-in-time queries, versioning, and data lineage.

## Architecture
The implementation is organized as a simple ETL flow:

`extract -> validate -> transform -> load`

Main modules:
- `app/services/extractor.py`: reads the `MASTER` sheet and builds a raw field dictionary
- `app/services/validator.py`: checks required fields and weight validity
- `app/services/transformer.py`: maps workbook labels to normalized output fields
- `app/services/loader.py`: enforces idempotency by file hash and writes uploads, companies, and snapshots
- `app/pipeline/orchestrator.py`: runs the end-to-end folder pipeline
- `app/api/routes.py`: exposes query endpoints over the warehouse tables

## Data Model
The warehouse uses three tables:

- `dim_company`: company master data
- `dim_upload`: uploaded file metadata and file hash
- `fact_snapshot`: versioned rating snapshot linked to company and upload

Temporal tracking is handled in `fact_snapshot` with:
- `valid_from`
- `valid_to`
- `is_current`

When a newer version of the same company is loaded, the previous current snapshot is closed and a new current snapshot is inserted.

The model guarantees exactly one current snapshot per company at any time.

## Key Design Decisions
- SCD Type 2 for historical tracking
- file hash deduplication for idempotency
- modular ETL design for clarity and testability
- PostgreSQL as warehouse backend
- FastAPI for lightweight analytics API

## Pipeline Behavior
The pipeline processes `.xlsm` files from the `data/` folder in sorted order.

Implemented behavior:
- reads only the `MASTER` worksheet
- parses labels from column 2 and values from column 3
- skips non-`.xlsm` files
- validates required fields before loading
- processes only new files based on file hash (incremental ingestion)
- avoids duplicate processing by hashing file contents
- logs file status, validation results, insert/update actions, and total execution time

## Data Lineage
The pipeline maintains lineage from source file to warehouse:

`source file -> dim_upload -> fact_snapshot`

Each snapshot is linked to:
- `file_name`
- `file_hash`
- `uploaded_at`

## Data Quality
Each processed file produces a validation report:

```json
{
  "valid": true,
  "errors": [],
  "warnings": [],
  "summary": {
    "fields_checked": 30,
    "fields_present": [
    ]
  }
}
```

## API
Implemented endpoints:

- `GET /companies`
- `GET /companies/{id}`
- `GET /companies/{id}/versions`
- `GET /companies/{id}/history`
- `GET /companies/compare`
- `GET /snapshots`
- `GET /snapshots/{id}`
- `GET /snapshots/latest`
- `GET /uploads`
- `GET /uploads/{upload_id}`
- `GET /uploads/stats`

These endpoints support listing current entities, viewing version history, comparing point-in-time snapshots, and auditing uploads.

## Running
Start the stack:

```bash
docker-compose up --build
```

Run the pipeline:

```bash
docker exec -it data_engineer_task-api-1 \
python -m app.pipeline.orchestrator
```

The API is exposed on `http://localhost:8000`.

Swagger documentation is available at `http://localhost:8000/docs#/`.

## Testing
Run the test suite inside the API container:

```bash
docker exec -it data_engineer_task-api-1 poetry run pytest
```

Coverage:
- unit tests (transform, validation)
- pipeline tests (idempotency, versioning)
- API tests (endpoints)
- integration tests (real Excel files + DB)

## Example API Outputs
Example current snapshots:

```json
[
  {
    "id": 2,
    "company_id": 1,
    "industry_score": "BBB",
    "currency": "EUR",
    "year_end": "December",
    "is_current": true
  }
]
```

Example upload stats:

```json
{
  "total_uploads": 4
}
```

Example company history:

```json
[
  {
    "industry_score": "A"
  },
  {
    "industry_score": "BBB"
  }
]
```

## Pipeline Observability
The pipeline logs:
- file processing status
- validation failures
- insert/update actions
- total execution time

## Scope
The implementation focuses on core ingestion, versioning, and query capabilities required by the assignment, with a lean and maintainable design.

## Limitations / Future Improvements

- Extend validation rules (range checks, schema enforcement)
- Add retry/backoff and failure handling in pipeline
- Introduce orchestration state tracking (e.g. Airflow/metadata store)
- Expand API filtering and querying capabilities

## Deliverables

- Source code (modular ETL pipeline and FastAPI service)
- Docker Compose setup (PostgreSQL + API)
- Data warehouse (dimensional model with SCD Type 2 snapshots)
- Test suite (unit, API, pipeline, and integration tests)

- Sample outputs (under `outputs/`):
  - `outputs/api/` — 10 example API calls with responses
  - `outputs/pipeline.log` — pipeline execution logs
  - `outputs/data_quality.json` — validation report example

- AI usage disclosure (see `AI_USAGE.md`)
