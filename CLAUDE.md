# Project Template — Claude Code Rules

**PROJECT_NAME** is a ... (describe your project here).

**Project Path:** `/path/to/project`

## Quick Reference

```
VERSION                 # App version (MAJOR.MINOR), Source of Truth
DECISIONS.md            # Architecture Decision Log (ALWAYS maintain!)
README.md               # Operations, Deployment, Setup
app/                    # Main code
├── main.py            # Application entrypoint
├── database.py        # SQLAlchemy models + migrations
├── utils.py           # Timezone, datetime helpers
├── strings.py         # i18n (DE/EN)
├── tests/             # pytest tests
├── templates/         # Jinja2 templates (if needed)
└── Dockerfile         # Container definition
```

---

## Important Rules

### 0. Before every action: Merge main!

**ALWAYS merge `main` into the current branch first:**
```bash
git fetch origin main && git merge origin/main --no-edit
```

This ensures:
- No merge conflicts
- All current changes are considered
- The branch is up to date

### 0b. Document decisions!

**Every architecture or design decision MUST be documented in [`DECISIONS.md`](DECISIONS.md).**

This applies to:
- New system behaviours
- Weighed alternatives (e.g., "No custom ML model because...")
- Design decisions that could be discussed repeatedly
- Anything marked "FINAL" or "do not change"

**Format**: See existing entries in `DECISIONS.md` — every decision needs a date, reasoning, rejected alternatives, and status (FINAL/TENTATIVE).

> **IMPORTANT for Claude**: When you make a decision or the user confirms one → enter it in `DECISIONS.md` IMMEDIATELY, not at the end!

### 1. Database Changes

**ALWAYS in `database.py`:**

1. **New table**: Add Model class → auto-created via `Base.metadata.create_all()`
2. **New column**: Extend Model AND add migration in `migrate_schema()`:
   ```python
   conn.execute(sqltext("ALTER TABLE IF EXISTS tablename ADD COLUMN IF NOT EXISTS column_name TYPE DEFAULT value;"))
   ```
3. **Idempotent**: Use `IF NOT EXISTS` / `IF EXISTS`

### 2. Update Dockerfile

**For new Python files**: Extend `app/Dockerfile`:
```dockerfile
COPY new_file.py .
```

### 3. Write Tests

**New features need tests in `app/tests/`:**
- Filename: `test_<feature>.py`
- Use fixtures from `conftest.py` (`db_session`)
- Async tests with `@pytest.mark.asyncio`
- Use `@pytest.mark.parametrize` instead of loops

#### Test Categories

| Category | Files | External? | When? |
|----------|-------|-----------|-------|
| **Unit tests** | `test_*.py` | No | Always (`pytest`) |
| **Integration** | `test_*_integration.py` | Maybe | Marked with `@pytest.mark.integration` |

### 4. New Python Packages

**External packages** (not in Python standard library) must go in `app/requirements.txt`:
```
new-package==1.2.3
```

**Standard library** (os, re, json, random, hashlib, datetime, etc.) needs no entry.

### 5. Versioning

**Source of Truth**: `VERSION` in the repo root (format: `MAJOR.MINOR`, e.g., `1.3`)

- **Minor bump**: Automatic via GitHub Action on merge to `main`
- **Major bump**: Only for breaking changes
- **IMPORTANT for Claude**: NEVER perform major bumps independently! Always **ASK the user first**.

---

## Code Patterns

### Session Handling
```python
from sqlalchemy.orm import Session
from database import engine

with Session(engine) as s:
    # DB operations
    s.commit()  # EXPLICIT commit!
```

### i18n
```python
from strings import get_text
message = get_text("key", lang, var=value)
```

### Date/Time
```python
from utils import today_str, now_utc, local_today
# today_str() → "2026-01-17" (local date)
# now_utc()   → datetime with UTC timezone
# Day starts at 04:00 (sleep adjustment)
```

---

## Timezone & Scheduler

**CRITICAL**: All time-based functions must respect the local timezone!

### Timezone Configuration

| Component | Configuration |
|-----------|---------------|
| `utils.LOCAL_TZ` | `tz.gettz(os.getenv("TZ", "Europe/Berlin"))` |
| Docker | `TZ=Europe/Berlin` in environment |

### Common Timezone Mistakes

1. **Scheduler runs in UTC instead of local** → forgot `Defaults(tzinfo=...)`
2. **Naive vs. aware datetimes** → always use `now_utc()` for timestamps, `local_today()` for date logic
3. **4am boundary ignored** → `local_today()` returns yesterday before 4am

---

## Test Execution

```bash
# All tests
cd app && pytest

# Specific tests
pytest tests/test_example.py -v

# Only changed tests (fast)
pytest --testmon

# With coverage
pytest --cov=. --cov-report=html
```

**Test fixtures** (`conftest.py`):
- `db_session` — In-memory SQLite

---

## Checklist for Changes

- [ ] New Python file? → `Dockerfile` update
- [ ] New external Python package? → `requirements.txt` update
- [ ] New DB table? → Model in `database.py`
- [ ] New DB column? → Model + migration in `migrate_schema()`
- [ ] New feature? → Tests in `app/tests/`
- [ ] User-facing text? → In `strings.py` (DE + EN)
- [ ] Time-based logic? → Use `utils.local_today()` / `utils.now_utc()`, NOT `datetime.now()`
- [ ] Breaking change? → **Ask user first!** Then bump `VERSION` manually to next major (e.g., `2.0`)
- [ ] Architecture/design decision? → Document in `DECISIONS.md`!
