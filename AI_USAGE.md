# AI Coding Assistance Disclosure

This assignment requires transparency about AI tool usage during development.

## Instructions
Please complete the sections below honestly. Using AI tools is **acceptable and expected**. We want to understand **how** you used them.


## 1. AI Tools Used

| Tool | Model | Usage |
|------|-------|-------|
| Claude Code (Anthropic) | Claude Sonnet 4.6 | Primary assistant throughout the project — used interactively via the CLI/VSCode extension |


## 2. Components Assisted

- [x] Data extraction logic (Excel parsing, MASTER sheet)
- [x] Data modeling design (ERD, table schemas, SCD Type 2)
- [x] ETL pipeline implementation
- [x] Data validation framework
- [x] API endpoint development (FastAPI)
- [x] Docker/Docker Compose configuration
- [x] SQL queries and migrations
- [x] Testing (unit/integration tests)
- [x] Documentation (README, Solution.md)
- [ ] Debugging specific issues
- [ ] Other: ___________


## 3. Detailed Description

### Data extraction logic
After manually exploring the `.xlsm` files in Excel and running an initial notebook to understand the MASTER sheet layout, I described the table boundaries (row ranges and column offsets) to Claude. Claude implemented the `extractor.py` helper functions (`_clean`, `_float`, `_year`, `_kv`) and the per-section extraction functions.

Later in the session I asked Claude to move the hardcoded row ranges out of Python into a separate `pipeline/table_config.yml` file, so that sheet layout changes require no code edits. Claude restructured all extractor functions to read bounds from that config.

### Data modeling (ERD + SCD Type 2)
I described the business need — tracking company rating snapshots over time with full history — and Claude proposed the SCD Type 2 pattern for `dim_company` (closing old rows with `valid_to`, opening new ones with `version+1`). I approved the model and Claude generated the SQLAlchemy ORM classes and the SQL DDL. I caught that `rating_methodologies` needed to be stored as `JSONB` rather than a plain string, which Claude had initially missed.

### ETL pipeline
My initial architecture thinking included Kafka or Airflow for file triggering, but Claude advised keeping it simple for the scope of the task — using `watchdog` for filesystem watching and `tenacity` for retries instead. I agreed, and Claude implemented the `runner.py` orchestration, `loader.py` SCD2 upsert logic, and `validator.py` rule engine.

### Data validation framework
I defined the validation rules (required fields, weight range 0–1, 3-letter ISO currency, at least one methodology). Claude translated these into the `Issue` / `ValidationReport` dataclasses and the `validate()` / `completeness()` functions.

### API endpoint development
I specified the required endpoints (list companies, get detail, version history, compare, scope timeseries, snapshots, uploads). Claude implemented them in FastAPI with the router/schema structure. I reviewed the response shapes and confirmed the field selection.

### Docker / Docker Compose
Claude wrote the `Dockerfile` and `docker-compose.yml`. I requested that the postgres health check gate the API container startup, which Claude added via `depends_on: condition: service_healthy`.

### SQL queries and migrations
Claude wrote the initial `init.sql`. Later I asked to split it into one file per table so changes are easier to review. Claude split it into 10 numbered files (`01_extensions.sql` → `10_views.sql`) and updated `docker-compose.yml` to mount the whole `sql/` directory so postgres runs them in order automatically.

### Testing
Claude wrote the full pytest suite (161 tests). I requested the tests be split into separate files by context (`test_extractor.py`, `test_validator.py`, `test_loader.py`, `test_runner.py`, `test_api.py`) with a shared `conftest.py`. Claude also moved the hardcoded test database path to a `TEST_DATABASE_URL` environment variable so the suite can be pointed at a real Postgres.

### Documentation
Claude wrote `Solution.md` based on the actual project state — covering Docker quickstart, local dev setup, all env vars, the full API reference, and the data model diagram.

### Environment variables
I asked Claude to move all hardcoded database connection values out of `api/database.py`. Claude split the single embedded URL into individual `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_POOL_SIZE`, `DB_MAX_OVERFLOW` env vars with safe defaults, and created `.env.example` documenting them.


## 4. Chat History / Logs

The full interaction with Claude Code is available in the session transcript. The conversation covered (in order):

1. Moving XLSM macro delimiters to `table_config.yml`
2. Writing a comprehensive pytest suite
3. Splitting the test suite into per-context files
4. Moving DB connection variables to environment variables
5. Splitting `init.sql` into per-table numbered files
6. Writing `Solution.md`
7. Writing this `AI_USAGE.md`

The git log on branch `HM_SOLUTION` reflects the incremental commits made throughout the session.


## 5. Self-Assessment

**What did AI do well?**

- Translated high-level architectural decisions into working code quickly and consistently.
- Kept the implementation pragmatic — it pushed back on over-engineering (Kafka, Airflow) and suggested simpler alternatives that fit the scope.
- Generated comprehensive test coverage without needing explicit test-case lists; it inferred edge cases from reading the source code.
- Refactoring tasks (splitting files, extracting env vars) were done cleanly without breaking existing behaviour — all 161 tests passed after every change.

**What did you need to correct or override?**

- Claude initially modelled `rating_methodologies` as a plain string. I corrected it to `JSONB` since the field holds a list of methodology names.
- The first suggestion for pipeline triggering included Kafka and Airflow. I overrode this in favour of a simpler `watchdog`-based solution appropriate for the task scope.
- The initial extractor had all row ranges hardcoded directly in Python. I directed Claude to extract them into `table_config.yml`.

**What did you implement entirely on your own?**

- Domain analysis: understanding the credit rating methodology by reading the XLSM files and researching the rating flow (Industry Risk → Business Risk → Financial Risk → Scope Credit Metrics → Final Rating).
- The initial data discovery notebook to validate field names and types before any code was written.
- All architectural decisions: choice of PostgreSQL, SQLAlchemy ORM, FastAPI, SCD Type 2 versioning, hash-based deduplication.
- Review and approval of every piece of generated code before committing.

**How did AI tools improve your development process?**

Reduced the time spent on boilerplate significantly — ORM models, Pydantic schemas, SQL DDL, and test fixtures that follow well-known patterns were generated in seconds rather than hours. This freed time to focus on the domain-specific decisions (sheet layout, validation rules, versioning strategy) that required actual understanding of the data.

**Were there any limitations or challenges with AI assistance?**

- Claude occasionally generated code that was correct in isolation but needed adjustment to match the existing project conventions (e.g. field naming, import order).
- Without explicit instruction, Claude tended toward slightly verbose implementations. Keeping prompts specific and reviewing each output before accepting was necessary to maintain code quality.


## 6. Recommendations

- **Start with domain understanding first.** AI tools are most effective once you know what you are building. Spending time with the raw data (opening the `.xlsm` files, sketching the ERD on paper) before involving AI produces much better prompts and avoids having to redo generated work.
- **Be the architect, use AI as the engineer.** Describe decisions clearly ("use SCD Type 2", "extract to YAML config") rather than asking AI to decide the architecture. The quality of output is directly proportional to the specificity of the input.
- **Review every output before committing.** AI-generated code is fast but not always aware of domain-specific constraints (e.g. JSONB vs VARCHAR for structured fields). Treat it as a first draft from a capable but context-limited colleague.
- **Use AI for refactoring and test coverage.** These are areas where AI provides high value with low risk — the before and after states are easy to verify, and the test suite can confirm nothing regressed.
- **Keep the feedback loop short.** Running tests after every AI-assisted change catches problems immediately, before they compound.


---

# Hajer's Development Notes

## 1. Data Discovery

Opening and checking the provided `.xlsm` files raised many questions about the credit rating analysis flow. The data is dummy so it was safe to upload one file to understand the domain terminology.

The rating methodology flows as follows:

```
Industry Risk Score + Weights
        ↓
Blended Industry Risk Profile
        ↓
  + Business Risk Profile (competitive position, profitability, diversification)
        ↓
  Combined Business & Industry Assessment
        ↓
  + Financial Risk Profile (leverage, coverage, liquidity ratios)
        ↓
  Preliminary Credit Rating
        ↓
  ± Scope Credit Metrics adjustments
        ↓
  Final Rating (AAA → D)
```

Reading the macro tables in the sheet revealed 7 distinct sections with fixed row/column boundaries. An initial notebook run with pandas confirmed the extraction outputs before writing any pipeline code.

## 2. Pipeline Design

Initial architecture thoughts:
- Pandas for file reading (PySpark for future scale), SQLAlchemy ORM, PostgreSQL as the database.
- Considered Kafka for file-trigger events and Airflow for scheduling — Claude advised keeping the solution simple and avoiding over-engineering for this scope. Agreed: used `watchdog` + `tenacity` instead.
- Uploaded one dummy file to generate field names and types for the data model.
- Caught that `rating_methodologies` must be `JSONB` (not a plain string) since it holds a list — Claude had initially missed this.

Thank you for your transparency!
