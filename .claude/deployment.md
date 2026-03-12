# Deployment Configuration

## Docker

- New source files → add `COPY` directive in `app/Dockerfile`.
- App containers run as non-root via `HOST_UID`/`HOST_GID` mapping:
  ```yaml
  user: "${HOST_UID:-1000}:${HOST_GID:-1000}"
  ```
- `redeploy.sh` exports `HOST_UID` and `HOST_GID` automatically.
- PostgreSQL (`db` service) remains unchanged — it manages its own user.

## i18n

```python
from strings import get_text
message = get_text("key", lang, var=value)
```

User-facing text must be added to `strings.py` in both DE and EN.
