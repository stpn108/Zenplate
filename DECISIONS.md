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

<!-- Add new decisions below -->

### 2026-04-30 — Scheduled tasks run via `ofelia` container

- **Decision**: All cron-style scheduled jobs are executed by an `ofelia` container that triggers commands inside other services via Docker labels.
- **Reasoning**: Centralises scheduling, keeps schedules declarative in compose, avoids in-app schedulers and host-level crontabs that bypass container isolation.
- **Rejected alternatives**: System crontab (host coupling), in-process schedulers like APScheduler (couples scheduling to app lifecycle), `sleep`-loop sidecars (no observability, no missed-run handling).
- **Status**: FINAL

### 2026-04-30 — Dashboards run in `grafana` container with host-bound port

- **Decision**: Any dashboard / metric visualisation is delivered through a `grafana` container, exposed to the host via the `PORTS_PREFIX` scheme.
- **Reasoning**: Grafana is unusable without a host-bound port; standardising on it avoids one-off dashboard implementations and keeps auth/storage consistent.
- **Rejected alternatives**: Custom Flask/Jinja dashboards (re-implementing solved problems), Prometheus expression browser only (insufficient UX), unbound Grafana (unreachable).
- **Status**: FINAL

### 2026-04-30 — `COMPOSE_PROJECT_NAME` defaults to empty

- **Decision**: `docker-compose.yml` declares `name: ${COMPOSE_PROJECT_NAME:-}` and `.env.example` ships an empty default.
- **Reasoning**: Empty value lets Docker Compose derive the project name from the working directory, which is what operators expect when cloning the template into a new project; a hardcoded `zenplate` default leaked the template name into derived projects.
- **Rejected alternatives**: Hardcoded `zenplate` default (template name leakage), removing the variable entirely (loses override capability).
- **Status**: FINAL

### 2026-04-30 — `merge-to-main.sh` stays on `main` by default

- **Decision**: After a successful merge, `merge-to-main.sh` remains on `main`. The original feature branch is fast-forwarded and pushed regardless. Pass `--return` to switch back to the feature branch.
- **Reasoning**: Most invocations are followed by deleting/abandoning the feature branch or starting fresh work from `main`; staying on `main` removes a manual `git switch main` step. The `--return` flag preserves the previous behaviour for users who want to keep iterating on the same branch.
- **Rejected alternatives**: Always return to the feature branch (previous default — extra step for the common case), introduce a separate script (duplicates logic).
- **Status**: FINAL
