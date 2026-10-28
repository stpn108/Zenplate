# Template Decisions (inherited from Zenplate)

These decisions are baked into the template. They explain why the
scaffolding looks the way it does and are **FINAL** for every project built
from Zenplate. They are not part of the project's own `DECISIONS.md`, which
starts empty at D-001. To deviate from one of them, add a project decision
that supersedes it and involve the mentor.

### T-001: Dockerfile copies `*.py`, tests excluded via `.dockerignore`

| | |
|---|---|
| **Decision** | `app/Dockerfile` uses `COPY *.py .`; `app/.dockerignore` excludes tests, caches and tooling. Non-Python assets still get explicit `COPY` lines. `tests/test_imports.py` imports every top-level module. |
| **In plain words** | A new code file can no longer be forgotten in the container build, which used to crash the app only after deployment. |
| **Reasoning** | ZenTallyBot D-029: every forgotten `COPY` produced a runtime ImportError in production. A template for non-technical owners must remove error classes rather than add checklist items. `CLAUDE.md` Rule 11 is satisfied automatically by the glob. |
| **Rejected alternatives** | (A) Per-file COPY lines plus a checklist item — the error class stays; (B) `COPY . .` — ships tests and tooling into the image |

### T-002: Numbered migrations with `schema_migrations` tracking and advisory lock, no Alembic

| | |
|---|---|
| **Decision** | `database.migrate_schema()` takes a Postgres advisory lock, runs `create_all()`, then applies every `(version, func)` in `MIGRATIONS` not yet recorded in `schema_migrations`, in one transaction. Migrations are append-only, idempotent and never `commit()`. SQLite runs the same path without the lock. |
| **In plain words** | Database changes are applied exactly once, in order, and a failed change is undone completely. Several app copies can start at once without breaking each other. |
| **Reasoning** | ZenTallyBot D-031 and D-110. Forbidding `commit()` inside migrations removes the need for a non-committing connection proxy. |
| **Rejected alternatives** | (A) Alembic — autogenerate drift, a second CLI and config surface; (B) inline `ALTER … IF NOT EXISTS` without tracking — no record, no rollback |

### T-003: Database backups as a Compose service running `pg_dump` in a loop

| | |
|---|---|
| **Decision** | Service `db-backup` runs `scripts/db-backup.sh` every `BACKUP_INTERVAL` (default 4h) into `./volumes/backups`, pruning after `BACKUP_RETENTION_DAYS` (default 7). |
| **In plain words** | The database is saved automatically every few hours, so a mistake can be undone by going back to an earlier copy. |
| **Reasoning** | ZenTallyBot depends on an ofelia daemon shared with another project on the host; invisible in the repo. A loop inside Compose has no external dependency and shows up in `docker compose ps`. |
| **Rejected alternatives** | (A) ofelia labels — needs a daemon outside this repo; (B) host cron — invisible, lost on server rebuild |

### T-004: Container health = database reachable; deploy verifies the running commit

| | |
|---|---|
| **Decision** | `app` has a Docker healthcheck running `python healthcheck.py` (`SELECT 1`). `redeploy.sh` waits for `healthy` and verifies the running `GIT_COMMIT` equals the built one; either failing aborts with exit 1. |
| **In plain words** | After every deployment the script checks that the new version is actually running and can talk to the database. |
| **Reasoning** | `CLAUDE.md` Rule 11 requires health checks. ZenTallyBot D-156: a service ran a stale image for weeks because the check only warned. A DB probe works for any app type. |
| **Rejected alternatives** | (A) HTTP `/health` — only for web apps; (B) `pgrep` — proves a process exists, not that it works; (C) warning instead of failure |

### T-005: Written, approved requirement before code (owner mode)

| | |
|---|---|
| **Decision** | In `owner` mode every behaviour change starts as `requirements/REQ-NNN-<slug>.md`, drafted by Claude, read back in plain language, set to `APPROVED` by the owner before implementation. Acceptance criteria map 1:1 to tests. In `developer` mode the requirement file is recommended, not required. |
| **In plain words** | Nothing gets built until it is written down in a way the owner has read and confirmed. |
| **Reasoning** | A non-developer owner cannot compare "what was meant" with "what was built" in code. The written requirement is the only place where that comparison is possible. |
| **Rejected alternatives** | (A) GitHub issues — outside the repo, not versioned with the code; (B) one `REQUIREMENTS.md` — unbounded, no per-feature status; (C) no gate |

### T-006: Repository content in English, conversation in the owner's language

| | |
|---|---|
| **Decision** | Files are English (`CLAUDE.md` Rule 1); the verbatim "Owner ask" keeps the owner's language; Claude talks to the owner in their language; `RELEASE_NOTES.md` is DE + EN; every decision has an "In plain words" row. |
| **In plain words** | Project files are in English so they stay consistent; talking to you happens in your language. |
| **Reasoning** | Rule 1 is immutable. ZenTallyBot's log became bilingual over time; a plain-words row avoids a second document. |
| **Rejected alternatives** | (A) owner-language files — violates Rule 1; (B) two versions of each file — drift |

### T-007: Release = merge a pull request on GitHub; the server tests and deploys automatically

| | |
|---|---|
| **Decision** | Claude opens a pull request for every change. `ci.yml` shows tests green or red on the PR. The owner merges on GitHub. On `main`, `version-bump.yml` bumps `VERSION`; when it completes, `deploy.yml` runs on a self-hosted runner on the server: `git pull` in `DEPLOY_DIR`, then `./redeploy.sh` (tests in the real test container, deploy only on green, verify health and commit). Deploy starts on completion of the bump run regardless of its outcome, and the bump treats a rejected push as a warning, so a version number can never block a deploy. Branch rules on `main` block force pushes and deletions only; a required check or PR requirement would only stop the version number from advancing. The gate is the server-side test run, not the Merge button. One runner per repository (personal accounts have no org runners); that is also what isolates several projects on one server. In `developer` mode `./merge-to-main.sh` and `./redeploy.sh` remain available as a terminal path. |
| **In plain words** | You release by clicking "Merge" on GitHub. The server then tests the new version itself and only switches over if every test passes. You never need a terminal. |
| **Reasoning** | The owner must not need a console. GitHub is the one interface they have: PR, checks, merge button, Actions log. ZenTallyBot's webhook receiver (D-039/D-041) was deprecated: custom HTTP server, systemd, token auth, lock. A self-hosted runner is outbound-only, needs no secrets in the repo, and reuses `redeploy.sh` so manual and automatic deploys are identical. Triggering on completion of the bump workflow gives exactly one deploy per merge with the final `VERSION`. |
| **Rejected alternatives** | (A) webhook receiver — the deprecated design; (B) SSH from GitHub-hosted runners — private key in secrets, inbound SSH; (C) cron `git pull` on the server — no visibility for the owner; (D) tests only on GitHub-hosted runners — not on the server; (E) owner runs scripts in a terminal — the requirement this template exists to remove |

### T-008: Release notes as `RELEASE_NOTES.md` (Markdown, DE + EN)

| | |
|---|---|
| **Decision** | User-facing changes go to `RELEASE_NOTES.md` in the repo root, newest first, one DE and one EN bullet per change, grouped by `VERSION`. |
| **In plain words** | One file lists, in everyday language, what changed for users in each version. |
| **Reasoning** | The checklist demanded release notes but no file existed. Markdown is readable on GitHub without tooling. |
| **Rejected alternatives** | (A) JSON like ZenTallyBot — needs an in-app renderer; (B) git releases — outside the repo, not bilingual. Switch to JSON if the project renders notes in-app. |

### T-009: `DATABASE_URL` is normalised to the psycopg 3 driver

| | |
|---|---|
| **Decision** | `database.normalize_database_url()` rewrites `postgresql://` and `postgres://` to `postgresql+psycopg://` before the engine is created. `.env.example` uses the explicit `postgresql+psycopg://` form. Other schemes (SQLite in tests) pass through unchanged. |
| **In plain words** | A normal database address now just works; before, a new project would not start because the database driver could not be found. |
| **Reasoning** | `requirements.txt` installs psycopg 3 only, but SQLAlchemy maps a plain `postgresql://` URL to psycopg2, so the template's own `.env.example` value raised `ModuleNotFoundError: psycopg2` at startup. Found while building voice-vault. Fixing it in code also repairs `.env` files that were copied from the old example. |
| **Rejected alternatives** | (A) only change `.env.example` — leaves existing `.env` files and hand-written URLs broken; (B) install psycopg2-binary as well — a second driver for the same database. |

### T-010: `merge-to-main.sh` never leaves the repository half-merged

| | |
|---|---|
| **Decision** | `merge-to-main.sh` runs under `set -e` and refuses to start while a merge is in progress (`MERGE_HEAD`) or tracked files have uncommitted changes. It syncs local `main` with origin (`--ff-only`) first, then dry-runs the merge (`--no-commit --no-ff`, then `--abort`). A conflict stops it before anything changed and lists the files and the commands to resolve them. Checked by `scripts/test_deploy_scripts.py`. |
| **In plain words** | Merging from the terminal either works completely or stops with clear instructions. It never leaves a half-finished merge behind. |
| **Reasoning** | ZenTallyBot D-185, from the trading bot (its D-215): with conflicting files `set -e` stopped mid-merge, the tree stayed in MERGING without instructions, and the next `git push` published something other than the merge. The logic is pure git and fits every project. |
| **Rejected alternatives** | (A) Resolve conflicts in favour of the branch automatically: right in the cherry-pick case, a guess in general; (B) no `set -e`: a hard stop becomes a silent run after a failed merge |

### T-011: `redeploy.sh` started from a terminal runs detached from it

| | |
|---|---|
| **Decision** | Started from a terminal, `redeploy.sh` re-runs itself with `setsid nohup` behind a `flock` on `/tmp/<directory>-redeploy.lock` and writes to `redeploy.log` (gitignored). The terminal only follows that log. The detached run ignores SIGHUP and writes its exit code as the last log line, which the terminal takes over. Ctrl-C is forwarded to the deploy's process group and aborts it (exit 130). A second start while one runs is refused. Only after a deploy that ended with 0 does the terminal follow `docker compose logs -f app`; Ctrl-C there just stops watching (exit 0). Without a terminal (the deploy pipeline) the script runs inline as before. Checked by `scripts/test_deploy_scripts.py`. |
| **In plain words** | A dropped SSH connection no longer stops a deploy halfway, with the app already stopped. Ctrl-C still does. |
| **Reasoning** | The deploy stops the app before it starts the new image. A hangup in between left the app down until someone noticed. From the AI video factory (its D-075) and ZenTallyBot (D-186, with the log following moved out of the detached run). SIGHUP and SIGINT are different signals, so the script can survive one and obey the other. |
| **Rejected alternatives** | (A) Tell the mentor to use `screen` or `tmux`: a habit, easily forgotten; (B) ignore SIGINT too: a deploy that goes wrong could not be stopped |

### T-012: `redeploy.sh` refuses to run while the shell overrides a key from `.env`

| | |
|---|---|
| **Decision** | Before anything else, `redeploy.sh` reads the keys of `.env` and aborts with exit 1 when the shell exports one of them with another value. The message names the keys and the `unset` command, never the values. Equal values pass. Quotes, a leading `export`, CRLF lines and an inline ` # comment` after an unquoted value are read as docker compose reads them. Checked by `scripts/test_deploy_scripts.py`. |
| **In plain words** | A setting left over in the terminal from another project can no longer slip into this deploy unnoticed. |
| **Reasoning** | docker compose takes an exported shell variable over the same key in `.env`. In ZenTallyBot (D-189) prod values left in a shell went into a staging deploy: the app got the prod database user, the next run the prod port. Several projects share one server here (`SETUP.md`), so the same can happen with `COMPOSE_PROJECT_NAME` or `PORTS_PREFIX`. Unlike ZenTallyBot, `.env.example` has inline comments, so the guard strips them: without that, an equal `PORTS_PREFIX` counted as different. |
| **Rejected alternatives** | (A) Unset the keys inside the script: would hide the mistake instead of naming it; (B) warn only: the deploy would still run with the wrong values |

### T-013: Images are built with the layer cache; `./redeploy.sh --no-cache` builds them anew

| | |
|---|---|
| **Decision** | `redeploy.sh` builds `app` with `docker compose build app`, so it reuses the layers `app-tests` was tested with. `app-tests` is rebuilt when `requirements.txt` changed. `--no-cache` rebuilds both without the build cache (and restarts the `app-tests` watcher); any other argument aborts with the usage line. The requirements hash is written only after a successful `app-tests` build. Checked by `scripts/test_deploy_scripts.py`. |
| **In plain words** | A normal deploy is faster and runs exactly the library versions the tests used. Fresh library versions come with `./redeploy.sh --no-cache`. |
| **Reasoning** | ZenTallyBot D-191 and the AI video factory D-251. The template used to build `app` with `--no-cache` on every deploy, while `app-tests` kept its cached layers until `requirements.txt` changed: the app could run newer versions of unpinned packages than the tests had seen. With the cache both normally reuse one `pip install` layer (until the build cache is pruned), and `--no-cache` refreshes both before the tests run. A failed `app-tests` build used to write the hash anyway, so every later deploy tested on the old image. |
| **Rejected alternatives** | (A) Keep `--no-cache` on every build: slower, and the app ran untested versions; (B) pin every dependency: the right long-term fix, a larger change per project (`checklist.md` asks for pins on new ones) |

### T-014: The tests run on four workers (pytest-xdist)

| | |
|---|---|
| **Decision** | `pytest-xdist==3.8.0` (MIT) in `app/requirements.txt`. `redeploy.sh` runs `pytest -n 4 --testmon`; the `app-tests` service runs its first pass with `-n 4` and the watcher with `ptw . --delay 2 --testmon -n 4 -v`. `app-tests` `mem_limit`/`memswap_limit` go from 512m to 1g. Checked by `scripts/test_deploy_scripts.py`. |
| **In plain words** | The tests run on four processes at once. Once a project has many tests, the deploy waits much less for them. |
| **Reasoning** | AI video factory D-250 (342 tests: 105 s → 31 s) and ZenTallyBot D-192 (1958 tests: 64 s → 22 s). testmon keeps its selection across the workers: a second run without a change runs no test and exits 0. The bare template (33 tests) takes 2.2 s on four workers against 0.6 s in one process, because starting the workers costs more than the tests; that turns around once a suite takes about 10 s. Measured here: four workers plus the controller peak at 337 MB; every worker holds its own interpreter, so the limit grows with the project. |
| **Rejected alternatives** | (A) `-n auto`: the worker count would follow the server's cores, and the memory limit could not be set for it; (B) xdist only when a project needs it: every project built from the template would have to rediscover it |
