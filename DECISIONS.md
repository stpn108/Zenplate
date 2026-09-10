# Architecture Decision Log

All architectural and design decisions are documented here.
Referenced from `CLAUDE.md` — Claude Code must know and maintain this log.

---

## How This Log Works

- **New decision?** → Add an entry **immediately**, in the same commit as the change.
- **IDs**: `D-NNN`, sequential. Next id = highest existing + 1. Never reuse,
  never renumber, never `D-XXX`. Check with `grep -o '^### D-[0-9]*' DECISIONS.md | sort | tail -1`.
- **Status FINAL** → Do not change without explicit user request.
- **Status TENTATIVE** → Can be revised if new insights emerge.
- **Superseding**: never edit a FINAL decision's content. Add a new one and
  set the old one's status to `SUPERSEDED by D-NNN`.
- **Before changing behaviour**: grep this file for the affected area. A
  decision you did not read still binds you.
- **Size**: when this file passes ~100 KB, move `SUPERSEDED` and `DEPRECATED`
  entries to `DECISIONS-ARCHIVE.md` (same format, ids unchanged). Claude
  cannot reliably read a 300 KB log every session.
- **Language**: English (`CLAUDE.md` Rule 1).

### Entry format

```markdown
### D-NNN: <Title> (FINAL | TENTATIVE)

| | |
|---|---|
| **Date** | YYYY-MM-DD |
| **Decision** | What was decided, precisely enough to implement from. |
| **In plain words** | One or two sentences the owner can read without technical background. |
| **Reasoning** | Why. Include the bug, measurement or constraint that triggered it. |
| **Rejected alternatives** | (A) … — why not; (B) … — why not |
| **Status** | **FINAL** / **TENTATIVE** / SUPERSEDED by D-NNN |
```

---

## Decisions

The entries D-001 to D-008 are inherited from the Zenplate template. They
apply to every project built from it; continue numbering from D-009.

### D-001: Dockerfile copies `*.py`, tests excluded via `.dockerignore` (FINAL)

| | |
|---|---|
| **Date** | 2026-09-10 |
| **Decision** | `app/Dockerfile` uses `COPY *.py .` instead of one `COPY` line per module. `app/.dockerignore` excludes `tests/`, `conftest.py`, `test_*.py`, `pytest.ini`, `pyproject.toml`, caches. Non-Python assets still get explicit `COPY` lines. `tests/test_imports.py` imports every top-level module so a broken module fails the suite. |
| **In plain words** | A new code file can no longer be forgotten in the container build, which used to crash the app only after deployment. |
| **Reasoning** | ZenTallyBot D-029: every forgotten `COPY` produced a runtime ImportError in production. A template aimed at non-technical owners must remove error classes rather than add checklist items. `CLAUDE.md` Rule 11 ("new source file → COPY directive") is satisfied automatically by the glob. |
| **Rejected alternatives** | (A) Keep per-file COPY lines plus the checklist item — the error class stays; (B) `COPY . .` — ships tests, caches and tooling into the production image |
| **Status** | **FINAL** |

### D-002: Numbered migrations with `schema_migrations` tracking and advisory lock, no Alembic (FINAL)

| | |
|---|---|
| **Date** | 2026-09-10 |
| **Decision** | `database.migrate_schema()` takes a Postgres transaction-level advisory lock, runs `create_all()`, then applies every `(version, func)` in `MIGRATIONS` that is not yet recorded in `schema_migrations`, all in one transaction. Migrations are append-only, idempotent DDL and never call `commit()`. SQLite (tests) runs the same path without the lock. `tests/test_migrations.py` covers apply-once, skip-applied, rollback-on-failure. |
| **In plain words** | Database changes are applied exactly once, in order, and a failed change is undone completely instead of leaving the database half-changed. Several app copies can start at the same time without breaking each other. |
| **Reasoning** | ZenTallyBot D-031 (tracking) and D-110 (advisory lock; concurrent `create_all()` on a fresh Postgres collides on `pg_type`). The template previously had an empty `migrate_schema()` and a rules file that demanded versioning without providing it. Forbidding `commit()` inside migrations removes the need for ZenTallyBot's `_NonCommittingConnection` proxy. |
| **Rejected alternatives** | (A) Alembic — autogenerate drift, a second CLI and config surface, too much for a one-service project run by a non-developer; (B) Inline `ALTER … IF NOT EXISTS` without tracking — no record of what ran where, no rollback |
| **Status** | **FINAL** |

### D-003: Database backups as a Compose service running `pg_dump` in a loop (FINAL)

| | |
|---|---|
| **Date** | 2026-09-10 |
| **Decision** | Service `db-backup` (image `postgres:16`, non-root, `mem_limit` 64m) runs `scripts/db-backup.sh` every `BACKUP_INTERVAL` (default 4h) into `./volumes/backups`, pruning dumps older than `BACKUP_RETENTION_DAYS` (default 7). Restore procedure documented in `.claude/operations.md`. |
| **In plain words** | The database is saved automatically every few hours, so a mistake can be undone by going back to an earlier copy. |
| **Reasoning** | The template had no backup at all. ZenTallyBot uses an ofelia cron daemon shared with another project on the same host; that dependency is server-specific and invisible in the repo (documented as a trap in its `deployment.md`). A plain loop inside Compose has no external dependency and is visible in `docker compose ps`. |
| **Rejected alternatives** | (A) ofelia labels — needs a daemon outside this repo; (B) host cron — invisible to the repo, lost on server rebuild; (C) no backup — unacceptable for an owner who cannot recover data by hand |
| **Status** | **FINAL** |

### D-004: Container health = database reachable (`healthcheck.py`) (FINAL)

| | |
|---|---|
| **Date** | 2026-09-10 |
| **Decision** | The `app` service has a Docker healthcheck running `python healthcheck.py`, which executes `SELECT 1` through the app's engine and exits 1 on failure. `redeploy.sh` waits for `healthy` and then verifies the running container's `GIT_COMMIT` equals the commit just built; either failing aborts with exit 1. |
| **In plain words** | After every deployment the script checks that the new version is actually running and can talk to the database. If not, the deployment is reported as failed instead of silently running old code. |
| **Reasoning** | `CLAUDE.md` Rule 11 requires health checks; the template had none for `app`. ZenTallyBot D-156: a service ran a stale image for weeks because the post-deploy check only warned. A DB probe works for any app type (bot, web, worker), unlike an HTTP probe. |
| **Rejected alternatives** | (A) HTTP `/health` — only exists for web apps; (B) `pgrep python` — proves a process exists, not that it works; (C) warning instead of hard failure on commit mismatch — the failure mode D-156 was written about |
| **Status** | **FINAL** |

### D-005: Written, approved requirement before code (FINAL)

| | |
|---|---|
| **Date** | 2026-09-10 |
| **Decision** | Every behaviour change starts as `requirements/REQ-NNN-<slug>.md` (template in `requirements/TEMPLATE.md`), drafted by Claude from the owner's words, read back in plain language, and set to `APPROVED` by the owner before implementation. Acceptance criteria map 1:1 to tests. Exceptions are listed in `.claude/collaboration.md` §2. Ideas that are not yet requirements live in `Roadmap.md`. |
| **In plain words** | Nothing gets built until it is written down in a way the owner has read and confirmed. That written version is what the tests check. |
| **Reasoning** | The owner of a Zenplate project is not a developer and does not review code. The only place where "what was meant" and "what was built" can be compared is a written requirement in plain language. Without it, Claude builds what it understood, and drift is discovered in production. |
| **Rejected alternatives** | (A) Issues on GitHub — outside the repo, not versioned with the code, owner needs another tool; (B) One `REQUIREMENTS.md` — grows unbounded, merge conflicts, no per-feature status; (C) No gate, rely on conversation — the failure mode this template exists to prevent |
| **Status** | **FINAL** |

### D-006: Repository content in English, conversation in the owner's language (FINAL)

| | |
|---|---|
| **Date** | 2026-09-10 |
| **Decision** | `requirements/`, `.claude/*.md`, `DECISIONS.md`, `Roadmap.md` and code are English (`CLAUDE.md` Rule 1). The verbatim "Owner ask" quote inside a requirement keeps the owner's language. Claude talks to the owner in the owner's language. `RELEASE_NOTES.md` carries DE and EN for every entry. Every decision has an "In plain words" row for the owner. |
| **In plain words** | The files in the project are in English so they stay consistent and reusable; talking to you happens in your language, and release notes and decision summaries are readable without technical background. |
| **Reasoning** | Rule 1 is immutable. ZenTallyBot's German decision log shows the cost of mixing: later entries switched to English and the file is now bilingual. The plain-words row gives the owner access without a second document to maintain. |
| **Rejected alternatives** | (A) Owner-facing files in the owner's language — violates Rule 1, breaks template reuse; (B) Two versions of each file — will drift within weeks |
| **Status** | **FINAL** |

### D-007: Deploy pipeline via self-hosted GitHub Actions runner executing `redeploy.sh`; PRs optional (FINAL)

| | |
|---|---|
| **Date** | 2026-09-10 |
| **Decision** | `.github/workflows/deploy.yml` runs on a self-hosted runner (label `deploy`) on the production server after the `Auto-bump version` workflow completes on `main`. It pulls `main` in `vars.DEPLOY_DIR` and runs `./redeploy.sh`, which tests in the real test container and deploys only on green. `ci.yml` runs the suite on GitHub-hosted runners for non-main pushes and PRs as feedback only. Pull requests are optional (mentor review), not required. Concurrency group prevents overlapping deploys. Repository must be private. |
| **In plain words** | Releasing is one command (`./merge-to-main.sh`). The server then tests the new version itself and only switches over if every test passes. You see green or red on GitHub. |
| **Reasoning** | The user's requirement: tests must run on the server, then deploy. ZenTallyBot tried a webhook receiver (D-039/D-041, deprecated): a custom HTTP server, systemd unit, token auth and lock to maintain. A self-hosted runner is outbound-only, needs no secrets in the repo, gives GitHub-native logs and failure e-mails, and reuses the existing script so manual and automated deploys are identical. Triggering on `workflow_run` of the bump (instead of `push`) guarantees exactly one deploy per merge with the final `VERSION` baked in. |
| **Rejected alternatives** | (A) Webhook receiver on the server — the deprecated ZenTallyBot design; (B) SSH from a GitHub-hosted runner — private key in repo secrets, server must accept inbound SSH from GitHub IPs; (C) Cron `git pull && ./redeploy.sh` on the server — no visibility for the owner, custom notifications needed; (D) Tests only on GitHub-hosted runners — SQLite instead of the real container, not "on the server" |
| **Status** | **FINAL** |

### D-008: Release notes as `RELEASE_NOTES.md` (Markdown, DE + EN) (TENTATIVE)

| | |
|---|---|
| **Date** | 2026-09-10 |
| **Decision** | User-facing changes are recorded in `RELEASE_NOTES.md` in the repo root, newest first, one DE and one EN bullet per change, grouped by `VERSION`. Rules in `.claude/release-notes.md`. |
| **In plain words** | There is one file that lists, in everyday language, what changed for users in each version. |
| **Reasoning** | The checklist already demanded release notes but no file or rule existed. ZenTallyBot keeps `RELEASE_NOTES.json` because its web app renders it; the template does not know its UI, and Markdown is readable by the owner on GitHub without tooling. |
| **Rejected alternatives** | (A) JSON like ZenTallyBot — machine-friendly, owner-unfriendly, no renderer in the template; (B) Git tags/releases — outside the repo files, not bilingual |
| **Status** | **TENTATIVE** — switch to JSON if the project renders notes in-app |

<!-- Add new decisions below, continuing from D-009 -->
