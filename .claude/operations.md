# Operations — for the owner

Everything in this file is meant to be run by the project owner without
help. Each command is copy-paste ready. Run them in the project directory
on the server.

## Release a change

```bash
./merge-to-main.sh
```

Merges your current branch into `main` and pushes. The deploy pipeline on
the server then runs the tests and, if they pass, deploys. Watch it at
`https://github.com/<owner>/<repo>/actions`. Green = live. Red = nothing
was deployed, the old version keeps running; the log says which test
failed. Paste that log to Claude.

## Deploy by hand (no pipeline, or pipeline is broken)

```bash
./redeploy.sh
```

Same steps as the pipeline: tests, build, restart, verify. Aborts at the
first failure and leaves the running app untouched.

## Is the right version running?

```bash
./version.sh
```

Shows repo version vs. running version. "Redeploy needed" means the
server has newer code than the running container.

## Read the logs

```bash
docker compose logs -f app        # live, Ctrl+C to stop
docker compose logs --tail=200 app  # last 200 lines
```

## Restart without redeploying

```bash
docker compose restart app
```

## Something is down

1. `docker compose ps` — every service should say `running` / `healthy`.
2. `docker compose logs --tail=100 app` — the last lines usually name the cause.
3. `docker compose restart app`.
4. Still down: `./redeploy.sh` (rebuilds from the current code).
5. Still down: send the output of steps 1 and 2 to Claude, and tell the
   mentor.

## Backups

The `db-backup` service dumps the database every `BACKUP_INTERVAL`
(default 4h) into `volumes/backups/` and keeps `BACKUP_RETENTION_DAYS`
(default 7) days.

```bash
ls -lh volumes/backups/           # list backups
docker compose logs db-backup     # last backup runs
```

### Restore a backup

This replaces the live database. Stop the app first.

```bash
docker compose stop app
gunzip -c volumes/backups/backup_YYYY-MM-DD-HH-MM-SS.sql.gz \
  | docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
docker compose start app
```

Copy `volumes/backups/` somewhere off the server regularly; the backup
service protects against mistakes, not against losing the server.

## Environment (.env)

Secrets and settings live in `.env` next to `docker-compose.yml`. Never
commit it, never paste it into chat. `.env.example` lists every key.
After changing `.env`: `docker compose up -d` applies it.

## Who to call

| Situation | Do |
|-----------|----|
| Pipeline red, test failure | Paste the failing test output to Claude |
| App down, restart did not help | Mentor |
| Data looks wrong | Do NOT restore a backup on your own; ask the mentor |
| Need a new feature | Describe it to Claude; it will write a requirement and read it back |
