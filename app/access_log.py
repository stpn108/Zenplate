"""
Access log for HTTP services (T-015): one line per request, as a pure ASGI middleware.

Works for FastAPI, Starlette and any plain ASGI app; it imports no framework.

    app.add_middleware(AccessLogMiddleware)      # FastAPI / Starlette
    app = AccessLogMiddleware(app)               # plain ASGI

The line goes to the logger "access" at INFO. setup_logging() sends it to stdout (root logger)
and, with LOG_DIR set, to LOG_DIR/access.log. Switch off the server's own access log where this
middleware is installed (uvicorn: access_log=False / --no-access-log), or every request is logged twice.

Never logged: the query string (tokens, OAuth codes), bodies, cookies, Authorization.
The peer address is read from the ASGI scope and left untouched; X-Forwarded-For is only logged.

Environment:
  ACCESS_LOG_SKIP  comma-separated paths not logged (default "/health,/healthz")
  SERVICE_NAME     written as svc=… (default: the hostname)
"""
import logging
import os
import socket
import time

from utils import LOCAL_TZ, now_utc

access_log = logging.getLogger("access")


def _escape(value: str) -> str:
    """Keep one request on one line: escape backslash, double quote and control characters."""
    out = []
    for ch in value:
        if ch == "\\" or ch == '"':
            out.append("\\" + ch)
        elif ch.isprintable():
            out.append(ch)
        else:
            out.append(f"\\x{ord(ch):02x}")
    return "".join(out)


def _header(headers, name: bytes) -> str:
    """All values of one request header, joined by ", "; "-" when the header is missing."""
    values = [v.decode("latin-1") for k, v in headers if k.lower() == name]
    return _escape(", ".join(values)) if values else "-"


class AccessLogMiddleware:
    def __init__(self, app):
        self.app = app
        skip = os.getenv("ACCESS_LOG_SKIP", "/health,/healthz")
        self.skip_paths = frozenset(p.strip() for p in skip.split(",") if p.strip())
        self.service = os.getenv("SERVICE_NAME") or socket.gethostname()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("path") in self.skip_paths:
            await self.app(scope, receive, send)
            return

        received = now_utc().astimezone(LOCAL_TZ)
        start = time.perf_counter()
        # Without a response start the request failed; the server answers it with 500.
        response = {"status": 500, "bytes": 0}

        async def send_and_count(message):
            if message["type"] == "http.response.start":
                response["status"] = message["status"]
            elif message["type"] == "http.response.body":
                response["bytes"] += len(message.get("body", b""))
            await send(message)

        try:
            await self.app(scope, receive, send_and_count)
        finally:
            duration = time.perf_counter() - start
            headers = scope.get("headers", [])
            client = scope.get("client")
            access_log.info(
                '%s - - [%s] "%s %s HTTP/%s" %d %d "%s" "%s" xff="%s" rt=%.3f svc=%s',
                client[0] if client else "-",
                received.strftime("%d/%b/%Y:%H:%M:%S %z"),
                scope.get("method", "-"),
                _escape(scope.get("path", "-")),
                scope.get("http_version", "1.1"),
                response["status"],
                response["bytes"],
                _header(headers, b"referer"),
                _header(headers, b"user-agent"),
                _header(headers, b"x-forwarded-for"),
                duration,
                self.service,
            )
