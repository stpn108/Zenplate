# Deployment

## Architecture

```
docker-compose.yml
├── db          Postgres 16, healthcheck pg_isready
├── db-backup   pg_dump every BACKUP_INTERVAL into ./volumes/backups (scripts/db-backup.sh)
├── app         Production app (own image, no volume mount), healthcheck via healthcheck.py
└── app-tests   Test runner (same image, ./app mounted, pytest --testmon in watch mode)
```

- All app containers run as the host user via `HOST_UID`/`HOST_GID`
  (exported by `redeploy.sh`). Postgres manages its own user.
- Every service has `mem_limit` + `memswap_limit` so one runaway container
  cannot take the host down.
- `TZ` comes from `.env` (default `Europe/Berlin`).

## Docker image

- `Dockerfile` copies `*.py`; `.dockerignore` excludes tests and tooling.
  A new module never needs a Dockerfile change. Non-Python assets
  (templates, static files, data) DO need a `COPY` line.
- `APP_VERSION`, `GIT_COMMIT`, `BUILD_TIME` are build args baked in as env
  vars; `version.sh` and the post-deploy check read them.

## Deploy flow

```
Owner or Claude: work on a feature branch, push
Owner:           ./merge-to-main.sh
                   ├── merges branch → main, pushes
                   ├── waits for the version-bump workflow
                   └── fast-forwards the branch
GitHub Actions:  "Auto-bump version" (VERSION += 0.1)
                   └── on completion: "Deploy" on the self-hosted runner
Server (runner): cd $DEPLOY_DIR && git pull && ./redeploy.sh
                   ├── pytest --testmon in the app-tests container
                   ├── FAIL → stop, nothing deployed, workflow red
                   ├── build image while old app keeps running
                   ├── stop / rm / up -d app
                   └── wait healthy + verify GIT_COMMIT == built commit, else FAIL
```

- **No pull request is required.** PRs are used when the mentor wants to
  review; `.github/pull_request_template.md` structures them.
- `./redeploy.sh` is the only deploy path, manual or automated. Both behave
  identically.
- `ci.yml` runs the suite on GitHub-hosted runners for every non-main
  push and PR. It is feedback, not the gate: the gate is the server run.

## Self-hosted runner setup (once per server)

1. On the server, as the deploy user (the one owning the checkout and
   `volumes/`), install a GitHub Actions runner:
   Repo → Settings → Actions → Runners → New self-hosted runner. Add the
   label `deploy`. Install it as a service so it survives reboots.
2. The deploy user must be in the `docker` group.
3. Repo → Settings → Variables → Actions: `DEPLOY_DIR` = absolute path of
   the checkout (the directory with `docker-compose.yml`, `.env`, `volumes/`).
4. Keep the repository **private**. A self-hosted runner on a public repo
   executes code from anyone's pull request.
5. Test: merge a trivial change, watch Actions → Deploy.

## Scripts

| Script | Purpose |
|--------|---------|
| `redeploy.sh` | Tests → build → deploy → verify. Aborts on first failure. |
| `merge-to-main.sh` | Feature branch → main, waits for the version bump |
| `version.sh` | Repo version vs. running container |
| `scripts/db-backup.sh` | pg_dump + retention, run by the `db-backup` service |

## Network & security posture

- Ports are bound to `127.0.0.1` only. Anything reachable from outside goes
  through a reverse proxy on the host with TLS.
- **Every HTTP endpoint is treated as publicly reachable**, even when only
  a proxy should forward to it. Authenticate and validate accordingly.
- Secrets only in `.env` (never committed) or the platform's secret store.
- Deployment configuration (`docker-compose.yml`, `.github/`, scripts)
  changes need explicit approval (`CLAUDE.md` Rule 11).
