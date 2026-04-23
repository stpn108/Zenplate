# Architecture Decision Log

All architectural and design decisions are documented here.
Referenced from `CLAUDE.md` — Claude Code must know and maintain this log.

---

## How This Log Works

- **New decision?** → Add entry with date, reasoning, alternatives
- **Status FINAL** → Do not change without explicit user request
- **Status TENTATIVE** → Can be revised if new insights emerge
- **Claude Code**: For every architecture decision, check whether it needs to be documented here

---

## Decisions

### D-001: Major Version Bump Never Autonomous (FINAL)

| | |
|---|---|
| **Date** | 2026-02 |
| **Decision** | Claude Code may NEVER perform major bumps (e.g., 1.x → 2.0) independently. Always ask the user first |
| **Reasoning** | Major bumps signal breaking changes and have implications for deployment and user expectations |
| **Alternatives rejected** | Automatic major bumps on certain trigger criteria (too risky) |
| **Status** | **FINAL** |

### D-002: Day Boundary at 04:00 (FINAL)

| | |
|---|---|
| **Date** | 2026-02 |
| **Decision** | `local_today()` returns yesterday before 04:00. Entries after midnight count as the previous day |
| **Reasoning** | Users are active late at night — entries after midnight logically belong to the same day. 04:00 is a realistic sleep cutoff |
| **Alternatives rejected** | Midnight as boundary (unnatural), configurable cutoff (over-engineering) |
| **Status** | **FINAL** |

### D-003: Container User ID Mapping via HOST_UID/HOST_GID (FINAL)

| | |
|---|---|
| **Date** | 2026-02-27 |
| **Decision** | App-Container (`app`, `app-tests`) laufen mit der UID/GID des Host-Users über `user: "${HOST_UID:-1000}:${HOST_GID:-1000}"` in docker-compose.yml. Der `db`-Service bleibt unverändert (PostgreSQL verwaltet seinen eigenen User). `redeploy.sh` exportiert `HOST_UID` und `HOST_GID` automatisch. |
| **Reasoning** | Container liefen als root (UID 0), was Sicherheitsrisiken birgt und bei Volume-Mounts (z.B. `app-tests`) zu Dateiberechtigungsproblemen führt. Dateien, die im Container erzeugt werden, gehören nun dem Host-User. |
| **Alternatives rejected** | (1) `USER` Directive im Dockerfile — baked feste UID ins Image, nicht portabel zwischen Systemen. (2) UID/GID des `db`-Service ändern — würde PostgreSQL brechen, da es eigenen User/Berechtigungen verwaltet. (3) Variable `UID` statt `HOST_UID` — `UID` ist read-only in Bash und nicht exportierbar. |
| **Status** | **FINAL** |

### D-004: Immutable CLAUDE.md with Sub-Files (FINAL)

| | |
|---|---|
| **Date** | 2026-03-12 |
| **Decision** | `CLAUDE.md` becomes an immutable central file containing universal, language-agnostic development rules. It is hash-verified in CI/CD — any modification blocks the pipeline. Project-specific rules (DB patterns, deployment config, test setup, checklists) live in `.claude/*.md` sub-files that Claude Code loads automatically. |
| **Reasoning** | A single mutable file mixed universal rules with project-specific patterns, making it hard to enforce compliance and reuse across projects. Separating immutable rules from project-specific configuration enables: (1) CI/CD integrity checks via SHA-256 hash, (2) reusability of the core ruleset across repositories, (3) project teams can adapt sub-files without risking core rule drift. |
| **Alternatives rejected** | (1) Keep everything in one file — no integrity verification possible, rules and patterns intermingled. (2) Use `.claude.yaml` for config — Markdown is more readable and allows inline examples. (3) Use git hooks only — CI/CD hash check is more reliable and visible. |
| **Status** | **FINAL** |

### D-005: Centralized Logging Setup via utils.setup_logging() (FINAL)

| | |
|---|---|
| **Date** | 2026-04-16 |
| **Decision** | Logging is configured once at startup via `utils.setup_logging()`, which reads `LOG_LEVEL` from the environment. Modules obtain loggers via `logging.getLogger(__name__)`. `main.py` no longer configures `logging.basicConfig()` directly. |
| **Reasoning** | Centralizing logging setup in `utils.py` ensures a single source of truth for log format and level, makes `LOG_LEVEL` changes traceable, and prevents accidental re-configuration when modules are imported in tests. |
| **Alternatives rejected** | (1) Keep `logging.basicConfig()` in `main.py` — scattered, hard to override in tests. (2) Per-module `basicConfig()` calls — leads to duplicate handlers and inconsistent formats. |
| **Status** | **FINAL** |

### D-006: Ruff Linter with pytest-ruff Integration (FINAL)

| | |
|---|---|
| **Date** | 2026-04-16 |
| **Decision** | Ruff is the project linter, configured in `app/pyproject.toml`. `pytest-ruff` is added to `requirements.txt` so linting runs automatically on every `pytest` invocation. Rules enabled: Pyflakes (F), Runtime errors (E9), Deprecated features (W6). |
| **Reasoning** | Catches undefined names, syntax errors, and deprecated usage early. Running via pytest keeps linting in the same feedback loop as tests without requiring a separate CI step. Permissive ignores (F401, F841) keep noise low for a template project. |
| **Alternatives rejected** | (1) Flake8 — slower, less configurable, no pyproject.toml support natively. (2) Separate `ruff check .` step — decoupled from test run, easier to forget. |
| **Status** | **FINAL** |

### D-007: Docker Compose Infrastructure Hardening (FINAL)

| | |
|---|---|
| **Date** | 2026-04-16 |
| **Decision** | All Docker Compose services now have: (1) `x-logging` anchor with `json-file` driver, 10 MB max size, 3 rotated files. (2) `mem_limit` + `memswap_limit` (app/tests: 512 MB, db: 256 MB). (3) PostgreSQL healthcheck + `condition: service_healthy` on `app` dependency. (4) `name: ${COMPOSE_PROJECT_NAME:-zenplate}` at compose root. (5) Separate `app-ci-tests` service with `profiles: ["ci"]` for single-run CI execution. |
| **Reasoning** | (1) Without log rotation, long-running containers fill the disk. (2) Without memory limits, a misbehaving container can OOM the host. (3) Without healthchecks the app may connect to a not-yet-ready database. (4) Without a project name, Docker derives the name from the directory, causing conflicts when multiple instances run on the same host. (5) The watch-mode `app-tests` service never exits cleanly in CI; a dedicated `ci` profile service exits with the test result code. |
| **Alternatives rejected** | (1) `syslog` driver — requires a syslog daemon, adds external dependency. (2) Hard-coded memory limits in Dockerfile — not portable across environments. (3) `restart: on-failure` for db — `service_healthy` is more precise. |
| **Status** | **FINAL** |

### D-008: Code Owners and Branch Protection for `main` (FINAL)

| | |
|---|---|
| **Date** | 2026-04-23 |
| **Decision** | `.github/CODEOWNERS` declares `@stpn108` as the default code owner for all paths (`*`). Branch protection for `main` is configured via the GitHub UI/API (not committed to the repo) and requires: pull request before merge, at least one approving review, code-owner review required, stale reviews dismissed on new commits, conversations resolved, force-pushes and deletions blocked, linear history. Direct pushes to `main` are forbidden for everyone except repository admins (bypass only for emergencies). |
| **Reasoning** | CODEOWNERS enables automatic review requests and is the prerequisite for the "require review from code owners" protection rule. Branch protection on `main` enforces Rule 6 ("Never push to main/master directly") at the platform level, not just by convention. Keeping the protection settings outside the repo avoids accidental bypass by editing a file; the CODEOWNERS file is the only part that must live in git. |
| **Alternatives rejected** | (1) Organization-level ruleset — repo is personal, no org. (2) Commit a `rulesets.json` — GitHub does not consume such a file from the repo; it is applied via API only. (3) Skip CODEOWNERS and rely on pre-commit hooks — hooks are bypassable client-side and do not enforce reviews. |
| **Status** | **FINAL** |

<!-- Add new decisions below -->
