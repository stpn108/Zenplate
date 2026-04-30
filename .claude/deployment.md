# Deployment Configuration

## Docker

- New source files → add `COPY` directive in `app/Dockerfile`.
- App containers run as non-root via `HOST_UID`/`HOST_GID` mapping:
  ```yaml
  user: "${HOST_UID:-1000}:${HOST_GID:-1000}"
  ```
- `redeploy.sh` exports `HOST_UID` and `HOST_GID` automatically.
- PostgreSQL (`db` service) remains unchanged — it manages its own user.
- `COMPOSE_PROJECT_NAME` defaults to empty (`${COMPOSE_PROJECT_NAME:-}`) — Docker Compose then derives the project name from the directory. Document any deviation in `DECISIONS.md`.

## Scheduled Tasks

- Any cron-style or scheduled job MUST run via an `ofelia` container — do **not** add a system crontab, in-app scheduler, or `sleep`-loop sidecar.
- Schedules are declared as Docker labels on the target service (`ofelia.job-exec.<name>.schedule` / `.command`).
- Pin the image to a specific version tag (e.g. `mcuadros/ofelia:v0.3`), never `:latest`.
- Mount the Docker socket read-only: `/var/run/docker.sock:/var/run/docker.sock:ro`.
- Run with `restart: unless-stopped` and route logs through the shared `*default-logging` anchor.

## Dashboards

- Any dashboard requirement MUST be served by a `grafana` container — do **not** roll a custom UI for metrics/visualisation.
- Pin the image to a specific version tag (e.g. `grafana/grafana:11.3.0`), never `:latest`.
- Bind exactly one host port via `PORTS_PREFIX` (e.g. `127.0.0.1:${PORTS_PREFIX}030:3000`) — Grafana is unusable without a host-bound port.
- Run as non-root with `user: "${HOST_UID:-1000}:${HOST_GID:-1000}"`.
- Persist data via `./volumes/grafana:/var/lib/grafana` and ensure the directory is writable by the mapped UID/GID.
- Provide admin credentials via env vars (`GF_SECURITY_ADMIN_USER`, `GF_SECURITY_ADMIN_PASSWORD`) — never hardcode in the compose file.

## i18n

```python
from strings import get_text
message = get_text("key", lang, var=value)
```

User-facing text must be added to `strings.py` in both DE and EN.
