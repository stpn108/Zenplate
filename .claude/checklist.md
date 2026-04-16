# Change Checklist

Before completing any task, verify:

- [ ] New source file? → Update `Dockerfile` with `COPY` directive
- [ ] New external dependency? → Add to dependency file with pinned version
- [ ] New DB table? → Model in `database.py`
- [ ] New DB column? → Model + migration in `migrate_schema()`
- [ ] New feature? → Tests in `app/tests/`
- [ ] User-facing text? → In `strings.py` (DE + EN)
- [ ] Time-based logic? → Use `utils.local_today()` / `utils.now_utc()`, NOT `datetime.now()`
- [ ] Breaking change? → **Ask user first!** Then bump `VERSION` manually to next major
- [ ] Architecture/design decision? → Document in `DECISIONS.md`!
- [ ] Secrets or credentials? → Environment variable or secrets manager, NEVER hardcoded
- [ ] Never ever create or commit /.env! 
