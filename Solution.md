# Credit Rating Analytics — Solution

A data engineering pipeline that extracts corporate credit rating data from `.xlsm` files, stores it in PostgreSQL, and exposes it through a REST API.

---

## Table of Contents

1. [Architecture](#architecture)
2. [Prerequisites](#prerequisites)
3. [Quick Start (Docker)](#quick-start-docker)
4. [Local Development](#local-development)
5. [Environment Variables](#environment-variables)
6. [Running the Pipeline](#running-the-pipeline)
7. [API Reference](#api-reference)
8. [Running Tests](#running-tests)
9. [Project Structure](#project-structure)
10. [Data Model](#data-model)

---

## Architecture

```
.xlsm files
    │
    ▼
pipeline/extractor.py     reads the MASTER sheet using row/column bounds
    │                     defined in pipeline/table_config.yml
    ▼
pipeline/validator.py     checks required fields, weight ranges, currency format
    │
    ▼
pipeline/loader.py        writes to PostgreSQL:
    │                       • dim_company     (SCD Type 2 versioning)
    │                       • fact_company_snapshot
    │                       • fact_scope_timeseries
    │                       • validation_result
    │                       • processed_file  (deduplication)
    ▼
api/  (FastAPI)           serves the stored data via REST endpoints
```

The pipeline runs once on startup against all files in `DATA_DIR`, then watches for new `.xlsm` files via `watchdog`. The API and pipeline run concurrently inside the Docker container.

---

## Prerequisites

| Tool | Version |
|------|---------|
| Docker + Docker Compose | >= 24 |
| Python | >= 3.11 (local dev only) |
| PostgreSQL | >= 15 (local dev only) |

---

## Quick Start (Docker)

```bash
# 1. Clone and enter the project
git clone <repo-url>
cd data_engineer_task

# 2. Copy the example env file and fill in secrets
cp .env.example .env

# 3. Place your .xlsm files in the data/ directory
cp /path/to/your/*.xlsm data/

# 4. Start everything
docker compose up --build
```

The API is available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

To stop and remove volumes:

```bash
docker compose down -v
```

---

## Local Development

### 1. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Start PostgreSQL

```bash
docker compose up postgres -d
```

Or point to an existing instance by setting env vars (see [Environment Variables](#environment-variables)).

### 3. Initialise the database

```bash
# Run all SQL files in order against your database
for f in sql/0*.sql; do
  psql "$DATABASE_URL" -f "$f"
done
```

### 4. Run the pipeline

```bash
PYTHONPATH=. python pipeline/runner.py
```

### 5. Start the API

```bash
PYTHONPATH=. uvicorn api.main:app --reload --port 8000
```

---

## Environment Variables

Copy `.env.example` to `.env` and edit as needed. All variables have safe defaults so the app starts without a `.env` file, but `DB_PASSWORD` should always be set in production.

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `DB_USER` | `credit_user` | Database user |
| `DB_PASSWORD` | *(empty)* | Database password |
| `DB_NAME` | `credit_ratings` | Database name |
| `DATABASE_URL` | *(built from above)* | Full DSN — overrides individual vars |
| `DB_POOL_SIZE` | `10` | SQLAlchemy connection pool size |
| `DB_MAX_OVERFLOW` | `20` | SQLAlchemy max overflow connections |
| `DATA_DIR` | `/app/data` | Directory the pipeline watches for `.xlsm` files |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `TEST_DATABASE_URL` | `sqlite:///./test.db` | Database used by the test suite |

---

## Running the Pipeline

### Via Docker (automatic)

The pipeline runs automatically when the container starts. Drop `.xlsm` files into `data/` at any time — `watchdog` picks them up within a second.

### Manually (local)

```bash
PYTHONPATH=. DATA_DIR=./data python pipeline/runner.py
```

The pipeline:
1. Scans `DATA_DIR` for `*.xlsm` files
2. Skips files already processed (hash-based deduplication)
3. Extracts, validates, and loads each file
4. Retries failed files up to 3 times with exponential backoff
5. Records a `pipeline_run` summary row on completion

### Table detection config

Row and column bounds for each section of the MASTER sheet live in `pipeline/table_config.yml`. Edit that file when the sheet layout changes — no Python code needs touching.

```yaml
tables:
  company_info:
    rows: [1, 3]          # iloc row range
    fields:
      rated_entity: "Rated entity"
  ...
```

---

## API Reference

Base URL: `http://localhost:8000`  
All endpoints are read-only (`GET`).

### Health

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Service info |
| `GET` | `/health` | Database connectivity check |

### Companies

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/companies` | List latest snapshot per company |
| `GET` | `/companies?sector=&country=&currency=` | Filter by sector / country / currency |
| `GET` | `/companies/{company_id}` | Full detail for a company |
| `GET` | `/companies/{company_id}/versions` | All SCD versions |
| `GET` | `/companies/{company_id}/history` | Snapshots filtered by `from_date` / `to_date` |
| `GET` | `/companies/{company_id}/scope` | Scope credit metric timeseries |
| `GET` | `/companies/{company_id}/scope?metric=EBITDA` | Filter timeseries by metric name |
| `GET` | `/companies/compare?company_ids=a,b` | Side-by-side comparison (optionally `as_of_date`) |

### Snapshots

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/snapshots` | List all snapshots with optional filters |
| `GET` | `/snapshots/latest` | Latest snapshot per company |
| `GET` | `/snapshots/{snapshot_id}` | Single snapshot detail |

### Uploads

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/uploads` | Upload audit trail |
| `GET` | `/uploads/stats` | Aggregated counts (total, success, failed) |
| `GET` | `/uploads/{upload_id}/details` | Single upload detail including hash |
| `GET` | `/uploads/{upload_id}/validations` | Validation issues for an upload |
| `GET` | `/uploads/{upload_id}/file` | Download the original source file |

Full interactive documentation with request/response schemas: `http://localhost:8000/docs`

---

## Running Tests

Tests use SQLite in memory — no running database required.

```bash
# Run all tests
python -m pytest tests/ -v

# Run a specific module
python -m pytest tests/test_extractor.py -v
python -m pytest tests/test_validator.py -v
python -m pytest tests/test_loader.py    -v
python -m pytest tests/test_runner.py   -v
python -m pytest tests/test_api.py      -v
```

To run tests against a real PostgreSQL instead of SQLite:

```bash
TEST_DATABASE_URL="postgresql://user:pass@localhost:5432/test_db" python -m pytest tests/ -v
```

### Test layout

| File | What it covers |
|------|---------------|
| `tests/conftest.py` | Shared fixtures, DB setup, data builders |
| `tests/test_extractor.py` | Helper functions, table extractors, `table_config.yml` |
| `tests/test_validator.py` | Required fields, warnings, completeness scoring |
| `tests/test_loader.py` | `is_processed`, SCD2 upsert, `load_file` end-to-end |
| `tests/test_runner.py` | `run_pipeline` orchestration and `PipelineRun` records |
| `tests/test_api.py` | All REST endpoints, filters, and error responses |

---

## Project Structure

```
.
├── api/
│   ├── database.py          SQLAlchemy engine, session factory
│   ├── main.py              FastAPI app, CORS, router registration
│   ├── models.py            ORM models (DimCompany, FactUpload, …)
│   ├── schemas.py           Pydantic request/response schemas
│   └── routers/
│       ├── companies.py     /companies endpoints
│       └── views.py         /snapshots and /uploads endpoints
├── pipeline/
│   ├── extractor.py         Excel → dataclasses
│   ├── table_config.yml     Row/column bounds for each MASTER sheet section
│   ├── validator.py         Validation rules and completeness scoring
│   ├── loader.py            Dataclasses → PostgreSQL (SCD2, dedup)
│   └── runner.py            Orchestration, retries, file watcher
├── sql/
│   ├── 01_extensions.sql    pgcrypto
│   ├── 02_dim_company.sql   SCD Type 2 dimension
│   ├── 03_dim_date.sql      Date dimension (2010–2030)
│   ├── 04_fact_upload.sql   Upload audit trail
│   ├── 05_fact_company_snapshot.sql  Main fact table
│   ├── 06_fact_scope_timeseries.sql  Timeseries rows
│   ├── 07_validation_result.sql      Validation log
│   ├── 08_pipeline_run.sql           Pipeline run tracking
│   ├── 09_processed_file.sql         Deduplication
│   └── 10_views.sql         vw_company_current, vw_scope_timeseries
├── tests/
│   ├── conftest.py          Shared fixtures and helpers
│   ├── test_extractor.py
│   ├── test_validator.py
│   ├── test_loader.py
│   ├── test_runner.py
│   └── test_api.py
├── data/                    Drop .xlsm files here
├── .env.example             All configurable environment variables
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## Data Model

```
dim_date ──────────────────────────────────────────────────┐
dim_company (SCD2: one row per attribute version)          │
    │                                                      │
    └──► fact_company_snapshot ◄──── fact_upload ◄─────────┘
              │
              ├──► fact_scope_timeseries  (one row per metric/year)
              └──► validation_result      (one row per field checked)

pipeline_run    (one row per pipeline execution)
processed_file  (filename + hash for dedup)
```

`dim_company` uses **SCD Type 2**: when a company's sector, currency, or country changes, the current row is closed (`valid_to`, `is_current=false`) and a new row with `version+1` is inserted. `fact_company_snapshot` always references the correct version via `company_key`.


Hajer Mahjoub

email : hajertkd@gmail.com