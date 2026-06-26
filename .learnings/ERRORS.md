# Errors

Command failures and integration errors.

---

## [ERR-20260625-004] uv_cache_sandbox

**Logged**: 2026-06-25T23:10:20+08:00
**Priority**: low
**Status**: pending
**Area**: tests

### Summary
`uv run pytest -q` failed inside the sandbox because uv needed access to its user cache directory.

### Error
```text
Failed to initialize cache at `/Users/chenbin/.cache/uv`
Operation not permitted (os error 1)
```

### Context
- The same command succeeded after running with escalated permissions.
- Result after escalation: 9 passed, 1 skipped.

### Suggested Fix
When validating this project with `uv run`, allow access to uv's cache directory or configure a workspace-local uv cache.

### Metadata
- Reproducible: yes
- Related Files: pyproject.toml, uv.lock

---

## [ERR-20260625-003] pytest_collection

**Logged**: 2026-06-25T23:08:59+08:00
**Priority**: medium
**Status**: pending
**Area**: tests

### Summary
`pytest -q` stopped during test collection because the active Python environment does not have `PyPDF2` installed.

### Error
```text
ModuleNotFoundError: No module named 'PyPDF2'
```

### Context
- Command attempted to run the existing test suite after path configuration refactoring.
- Collection imported `backend.services.ai_service`, which imports `PyPDF2`.

### Suggested Fix
Run tests in the project-managed environment with dependencies from `pyproject.toml`, or install the missing dependency in the active environment.

### Metadata
- Reproducible: yes
- Related Files: backend/services/ai_service.py, pyproject.toml

---

## [ERR-20260625-002] postgres_engine_validation

**Logged**: 2026-06-25T23:08:16+08:00
**Priority**: medium
**Status**: pending
**Area**: tests

### Summary
Direct validation of the PostgreSQL `db_engine.py` branch failed because the active Python environment does not have `psycopg2` installed.

### Error
```text
ModuleNotFoundError: No module named 'psycopg2'
```

### Context
- Command attempted to load `backend/database/db_engine.py` with `settings.DB_TYPE = "postgresql"` to inspect `DATABASE_URL`.
- SQLAlchemy imports the PostgreSQL DBAPI while creating the engine, even without opening a database connection.

### Suggested Fix
Run validation in the project-managed environment that includes `psycopg2-binary`, or validate PostgreSQL URL construction separately from engine creation.

### Metadata
- Reproducible: yes
- Related Files: backend/database/db_engine.py, pyproject.toml

---

## [ERR-20260625-001] python_import_validation

**Logged**: 2026-06-25T22:57:21+08:00
**Priority**: medium
**Status**: pending
**Area**: tests

### Summary
Importing `backend.core.bootstrap` through the package path during a lightweight validation hit an existing circular import in `backend.core` and `backend.database`.

### Error
```text
ImportError: cannot import name 'validate_sub_payment_risk' from partially initialized module 'backend.core.finance_engine' (most likely due to a circular import)
```

### Context
- Command attempted to import `backend.core.bootstrap` and call `_describe_database_target`.
- The package initializer loaded unrelated core/database modules before the target file could be validated.

### Suggested Fix
Use a narrower test path for bootstrap helpers or remove the package-level circular import between `backend.core.finance_engine`, `backend.database.crud_finance`, and `backend.database.__init__`.

### Metadata
- Reproducible: yes
- Related Files: backend/core/__init__.py, backend/core/finance_engine.py, backend/database/__init__.py, backend/database/crud_finance.py

---
