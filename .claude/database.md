# Database Rules

## Schema Changes

**ALWAYS in `database.py`:**

1. **New table**: Add Model class → auto-created via `Base.metadata.create_all()`
2. **New column**: Extend Model AND add migration in `migrate_schema()`:
   ```python
   conn.execute(sqltext("ALTER TABLE IF EXISTS tablename ADD COLUMN IF NOT EXISTS column_name TYPE DEFAULT value;"))
   ```
3. **Idempotent**: Use `IF NOT EXISTS` / `IF EXISTS` for all DDL statements.
4. **Migrations:** Use versioned migrations AND inline structures like ADD TABLE ... IF NOT EXISTS or ALTER TABLE ... IF ...

## Session Handling

```python
from sqlalchemy.orm import Session
from database import engine

with Session(engine) as s:
    # DB operations
    s.commit()  # EXPLICIT commit!
```

## Date/Time

```python
from utils import today_str, now_utc, local_today
# today_str() → "2026-01-17" (local date)
# now_utc()   → datetime with UTC timezone
# Day starts at 04:00 (sleep adjustment)
```

**CRITICAL**: All time-based functions must respect the local timezone.

| Component | Configuration |
|-----------|---------------|
| `utils.LOCAL_TZ` | `tz.gettz(os.getenv("TZ", "Europe/Berlin"))` |
| Docker | `TZ=Europe/Berlin` in environment |

### Common Timezone Mistakes

1. **Scheduler runs in UTC instead of local** → forgot `Defaults(tzinfo=...)`
2. **Naive vs. aware datetimes** → always use `now_utc()` for timestamps, `local_today()` for date logic
3. **4am boundary ignored** → `local_today()` returns yesterday before 4am
