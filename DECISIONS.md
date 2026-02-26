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

<!-- Add new decisions below -->
