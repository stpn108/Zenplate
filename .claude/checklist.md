# Change Checklist

Before completing any task, verify:

- [ ] New source file? → Update `Dockerfile` with `COPY` directive
- [ ] New external dependency? → Add to dependency file with pinned version
- [ ] Using a new function from an existing package? → Check if it requires an **optional extra** (e.g. `[webhooks]`, `[hiredis]`)
- [ ] New DB table? → Model in `database.py`
- [ ] New DB column? → Model + migration in `migrate_schema()`
- [ ] New feature? → Tests in `app/tests/`
- [ ] New feature with data? → Which table logs it? `created_at` timestamp for time series?
- [ ] User-facing text? → In `strings.py` (DE + EN)
- [ ] Time-based logic? → Use `utils.local_today()` / `utils.now_utc()`, NOT `datetime.now()`
- [ ] Breaking change? → **Ask user first!** Then bump `VERSION` manually to next major
- [ ] User-visible change? → Add entry to release notes
- [ ] Architecture/design decision? → Document in `DECISIONS.md`!
- [ ] Secrets or credentials? → Environment variable or secrets manager, NEVER hardcoded
- [ ] Never ever create or commit /.env!
- [ ] Always make sure to update docker-compose.yml when new environment variables are introduced!
