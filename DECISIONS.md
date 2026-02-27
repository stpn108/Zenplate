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

<!-- Add new decisions below -->
