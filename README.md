# Project Template

A Docker-based Python project template with PostgreSQL, auto-versioning, and a tested deployment pipeline.

## Project Structure

```
VERSION                 # App version (MAJOR.MINOR), Source of Truth
DECISIONS.md            # Architecture Decision Log
CLAUDE.md               # Development rules for Claude Code
app/                    # Main code
├── main.py            # Application entrypoint
├── database.py        # SQLAlchemy models + migrations
├── utils.py           # Timezone, datetime helpers
├── strings.py         # i18n (DE/EN)
├── tests/             # pytest tests
├── templates/         # Jinja2 templates
└── Dockerfile         # Container definition
```

---

## Environment Variables

```env
# Required
DATABASE_URL=postgresql://user:pass@db/mydb

# Optional (with defaults)
TZ=Europe/Berlin
LOG_LEVEL=INFO
```

---

## Deployment

### Standard Deployment (with tests)

```bash
./redeploy.sh
```

The script:
1. Runs `pytest --testmon` (only changed tests)
2. On test failure → abort
3. On success → Stop, Remove, Build (--no-cache), Up
4. Shows logs (Ctrl+C to exit)

### Manual Deployment (without tests)

```bash
docker compose build app && docker compose up -d app
```

### Logs

```bash
docker compose logs -f app
```

### Check Version

```bash
./version.sh          # Compares repo version with running app
```

---

## Versioning

**Source of Truth**: `VERSION` in the repo root (format: `MAJOR.MINOR`, e.g., `1.3`)

**Display**: `v1.3 (abc1234)` — in startup log and optionally in UI.

- **Minor bump**: Automatic via GitHub Action on every merge to `main`
- **Major bump**: Manual — only for breaking changes. Change `VERSION` in branch before merge

---

## Development Workflow

### Merge to Main

```bash
./merge-to-main.sh
```

The script:
1. Merges current branch → `main`
2. Pushes and waits for version-bump GitHub Action
3. Pulls the bumped version
4. Fast-forwards feature branch to include the version bump

### Running Tests

```bash
# All tests
cd app && pytest

# With coverage
pytest --cov=. --cov-report=html

# Watch mode (re-runs on file change)
ptw . --delay 2 --testmon -v
```

### Docker Test Runner

The `app-tests` service mounts the source and continuously runs tests:

```bash
docker compose up -d app-tests
docker compose logs -f app-tests
```

---

## Docker Services

| Service | Purpose | Port |
|---------|---------|------|
| **db** | PostgreSQL 16 | internal |
| **app** | Main application | `127.0.0.1:8000:8000` |
| **app-tests** | Continuous test runner | — |

---

## Adding to This Template

1. Add application code to `app/`
2. Update `app/Dockerfile` with new COPY statements
3. Add external packages to `app/requirements.txt`
4. Write tests in `app/tests/`
5. Add user-facing strings to `app/strings.py`
6. Document architecture decisions in `DECISIONS.md`
