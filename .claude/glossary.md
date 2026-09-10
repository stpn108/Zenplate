# Glossary

The owner's words on the left, the code's names on the right. Fill in during
onboarding, extend before introducing any new domain name. This is the
contract that keeps conversation and code from drifting apart.

## Rules

- Before naming a table, column, function or string key for a domain
  concept: look here first. Reuse the existing name.
- A new term is added **before** the code that uses it, in the same
  commit.
- One term, one code name. If two names exist, one is a bug to fix.
- Code names derive from the English column; German-speaking owners get
  the German term in the "Owner says" column only.
- Definitions state what the owner means, not what the code does.

## Terms

| Owner says | Meaning | In code | Notes |
|------------|---------|---------|-------|
| <term> | <what the owner means by it> | `<table.column>`, `<function>()` | <edge cases, units, what it is NOT> |
| | | | |

## Units and formats

| Quantity | Unit | Stored as | Displayed as |
|----------|------|-----------|--------------|
| <e.g. weight> | <kg> | `Float` | `72.4 kg` |
| Dates | local day (04:00 boundary, see `code-patterns.md`) | `YYYY-MM-DD` string or `Date` | `DD.MM.YYYY` (DE) |
| Timestamps | UTC | `DateTime(timezone=True)` | local time |
