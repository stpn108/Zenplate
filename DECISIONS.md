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

<!-- Add new decisions below, starting with D-001 -->
