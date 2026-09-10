# Project Configuration

> Fill this in during the first session (skill: `onboarding`). Every placeholder
> in angle brackets must be replaced before the first feature is built.

**<PROJECT_NAME>** is a <one-sentence description in the owner's words>.

**Project Path:** `/path/to/project`

## What this project is NOT

Scope creep is the most common way a small project drifts. List what is
explicitly out of scope, so a request that lands here is escalated instead
of built:

- NOT a <e.g. "general chat bot">
- NOT a <e.g. "multi-tenant SaaS">
- NOT a <e.g. "replacement for the owner's accounting tool">

## People

| Role | Who | Responsibility |
|------|-----|----------------|
| **Owner** | <name> | Defines what the product does. Not a developer. Runs `./merge-to-main.sh` to release. |
| **Mentor** | <name> | Reviews architecture, decisions and risky changes. Reachable via <channel>. |
| **Claude** | — | Implements. Follows `CLAUDE.md`, this directory and `DECISIONS.md`. |

## Stack

- **Language**: Python 3.12
- **Database**: PostgreSQL 16 (SQLAlchemy 2.x, no ORM-generated migrations)
- **Web** (optional): FastAPI + Jinja2
- **LLM** (optional): see `.claude/llm.md`
- **Deployment**: Docker Compose on a single server, `./redeploy.sh`, GitHub Actions self-hosted runner
- **Tests**: pytest (+ ruff via `pytest --ruff`)

## Quick Reference

```
VERSION                 # App version (MAJOR.MINOR), source of truth
DECISIONS.md            # Architecture Decision Log (ALWAYS maintain!)
RELEASE_NOTES.md        # User-facing change log (DE + EN)
Roadmap.md              # Scoped-but-not-scheduled ideas
README.md               # Operations, deployment, setup
requirements/           # One file per approved requirement (REQ-NNN-<slug>.md)
app/                    # Main code
├── main.py            # Application entrypoint (calls migrate_schema())
├── database.py        # SQLAlchemy models + MIGRATIONS runner
├── healthcheck.py     # Docker health probe (DB reachable?)
├── utils.py           # Timezone, datetime, logging helpers
├── strings.py         # i18n (DE/EN)
├── tests/             # pytest tests
├── templates/         # Jinja2 templates (if needed)
└── Dockerfile         # Container definition (COPY *.py, no per-file lines)
scripts/db-backup.sh    # pg_dump loop, run by the db-backup service
```

## Where to read what

| Question | File |
|----------|------|
| How do I turn an owner request into work? | `.claude/requirements.md` |
| How do I talk to the owner, what do I ask before doing? | `.claude/collaboration.md` |
| Where does new code go, what must never be mixed? | `.claude/architecture.md` |
| What does the owner call things, what does the code call them? | `.claude/glossary.md` |
| DB schema, migrations | `.claude/database.md` |
| Session handling, i18n, dates, logging | `.claude/code-patterns.md` |
| Tests | `.claude/testing.md` |
| Docker, deploy pipeline, backups, network posture | `.claude/deployment.md` |
| Day-to-day operation for the owner | `.claude/operations.md` |
| HTTP API conventions | `.claude/api-design.md` |
| LLM integration | `.claude/llm.md` |
| Classic ML training | `.claude/machine-learning.md` |
| Release notes | `.claude/release-notes.md` |
| Before finishing any task | `.claude/checklist.md` |
