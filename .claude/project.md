# Project Configuration

> **ONBOARDING NOT DONE.** This file still contains `<placeholders>`.
> Before doing ANY other work in this repository, run the `onboarding`
> skill (`.claude/skills/onboarding/SKILL.md`): it asks the owner what the
> project is and which collaboration mode applies, and fills this file.
> Remove this banner when onboarding is complete.

**<PROJECT_NAME>** is a <one-sentence description in the owner's words>.

**Project Path:** `/path/to/project`

## Collaboration mode

**Mode:** `<owner | developer>`

| Mode | Who develops | How a change is released | Rules |
|------|--------------|--------------------------|-------|
| `owner` | Claude. The owner defines requirements and never uses a terminal. | Claude opens a pull request; the owner merges it on GitHub; the server tests and deploys. | `collaboration.md` and `requirements.md` are binding |
| `developer` | A developer, with Claude. | Developer's choice: PR merge on GitHub, or `./merge-to-main.sh` / `./redeploy.sh` in a terminal. | `collaboration.md` §2 and §6 are recommendations |

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
| **Owner** | <name> | Defines what the product does. Merges pull requests on GitHub. |
| **Mentor** | <name> | Reviews architecture and decisions, runs the server. Reachable via <channel>. |
| **Claude** | — | Implements. Follows `CLAUDE.md`, this directory and `DECISIONS.md`. |

## Stack

- **Language**: Python 3.12
- **Database**: PostgreSQL 16 (SQLAlchemy 2.x, numbered migrations)
- **Web** (optional): FastAPI + Jinja2
- **LLM** (optional): see `.claude/llm.md`
- **Deployment**: Docker Compose on one server; GitHub Actions self-hosted runner runs `./redeploy.sh`
- **Tests**: pytest (+ ruff via `pytest --ruff`)

## Quick Reference

```
VERSION                 # App version (MAJOR.MINOR), source of truth
DECISIONS.md            # Architecture Decision Log of THIS project (ALWAYS maintain!)
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
| Why is the template built this way? | `.claude/template-decisions.md` |
| DB schema, migrations | `.claude/database.md` |
| Session handling, i18n, dates, logging | `.claude/code-patterns.md` |
| Tests | `.claude/testing.md` |
| Docker, deploy pipeline, backups, network posture | `.claude/deployment.md` |
| Day-to-day operation (owner on GitHub, mentor in the terminal) | `.claude/operations.md` |
| HTTP API conventions | `.claude/api-design.md` |
| LLM integration | `.claude/llm.md` |
| Classic ML training | `.claude/machine-learning.md` |
| Release notes | `.claude/release-notes.md` |
| Before finishing any task | `.claude/checklist.md` |
