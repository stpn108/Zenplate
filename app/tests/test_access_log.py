"""
Tests for the access log middleware and the log files written with LOG_DIR (T-015).
"""
import datetime as dt
import logging
import logging.handlers
import re

import pytest

import access_log
import utils
from access_log import AccessLogMiddleware

LINE = re.compile(
    r'^(?P<peer>\S+) - - \[(?P<time>[^\]]+)\] "(?P<method>\S+) (?P<path>.*) HTTP/(?P<version>[\d.]+)" '
    r'(?P<status>\d{3}) (?P<bytes>\d+) "(?P<referer>.*)" "(?P<ua>.*)" xff="(?P<xff>.*)" '
    r'rt=(?P<rt>\d+\.\d{3}) svc=(?P<svc>\S+)$'
)


def make_app(status=200, body=(b"hello", b" world"), fail=False):
    async def app(scope, receive, send):
        if fail:
            raise RuntimeError("boom")
        await send({"type": "http.response.start", "status": status, "headers": []})
        for part in body:
            await send({"type": "http.response.body", "body": part, "more_body": True})
        await send({"type": "http.response.body", "body": b""})
    return app


async def request(app, path="/items/7", query=b"", headers=(), client=("203.0.113.5", 4711), scope_type="http"):
    scope = {"type": scope_type, "http_version": "1.1", "method": "GET", "path": path,
             "query_string": query, "headers": list(headers), "client": client}

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    sent = []

    async def send(message):
        sent.append(message)

    await app(scope, receive, send)
    return sent


@pytest.fixture
def access_lines(caplog, monkeypatch):
    monkeypatch.setenv("SERVICE_NAME", "web")
    monkeypatch.delenv("ACCESS_LOG_SKIP", raising=False)
    caplog.set_level(logging.INFO, logger="access")

    def lines():
        return [r.getMessage() for r in caplog.records if r.name == "access"]
    return lines


async def test_access_log_line_format(access_lines, monkeypatch):
    monkeypatch.setattr(access_log, "now_utc", lambda: dt.datetime(2026, 11, 12, 9, 30, 5, tzinfo=dt.timezone.utc))
    monkeypatch.setattr(access_log, "LOCAL_TZ", dt.timezone(dt.timedelta(hours=1)))
    ticks = iter([100.0, 100.25])
    monkeypatch.setattr(access_log.time, "perf_counter", lambda: next(ticks))
    headers = [(b"referer", b"https://example.org/"), (b"user-agent", b"curl/8.5"),
               (b"x-forwarded-for", b"198.51.100.9")]
    await request(AccessLogMiddleware(make_app()), headers=headers)
    assert access_lines() == [
        '203.0.113.5 - - [12/Nov/2026:10:30:05 +0100] "GET /items/7 HTTP/1.1" 200 11 '
        '"https://example.org/" "curl/8.5" xff="198.51.100.9" rt=0.250 svc=web'
    ]


async def test_access_log_drops_query_string(access_lines):
    await request(AccessLogMiddleware(make_app()), path="/oauth/callback", query=b"code=SECRET&state=abc")
    (line,) = access_lines()
    assert LINE.match(line)["path"] == "/oauth/callback"
    assert "SECRET" not in line and "?" not in line


@pytest.mark.parametrize("referer, expected", [
    (b"https://example.org/callback?code=SECRET&state=abc", "https://example.org/callback"),
    (b"https://example.org/page#access_token=SECRET", "https://example.org/page"),
    (b"https://example.org/a?x=SECRET#frag", "https://example.org/a"),
    (b"https://example.org/plain", "https://example.org/plain"),
])
async def test_access_log_drops_referer_query_and_fragment(access_lines, referer, expected):
    await request(AccessLogMiddleware(make_app()), headers=[(b"referer", referer)])
    (line,) = access_lines()
    assert LINE.match(line)["referer"] == expected and "SECRET" not in line


async def test_access_log_never_logs_cookie_or_authorization(access_lines):
    headers = [(b"cookie", b"session=COOKIE"), (b"authorization", b"Bearer TOKEN")]
    await request(AccessLogMiddleware(make_app()), headers=headers)
    (line,) = access_lines()
    assert "COOKIE" not in line and "TOKEN" not in line


async def test_access_log_missing_values_as_dash(access_lines):
    await request(AccessLogMiddleware(make_app()), client=None)
    m = LINE.match(access_lines()[0])
    assert (m["peer"], m["referer"], m["ua"], m["xff"]) == ("-", "-", "-", "-")


@pytest.mark.parametrize("status, body, expected_bytes", [
    (200, (b"hello", b" world"), 11),
    (404, (b"not found",), 9),
    (204, (), 0),
])
async def test_access_log_status_and_bytes(access_lines, status, body, expected_bytes):
    await request(AccessLogMiddleware(make_app(status=status, body=body)))
    m = LINE.match(access_lines()[0])
    assert (int(m["status"]), int(m["bytes"])) == (status, expected_bytes)


async def test_access_log_duration_present(access_lines):
    await request(AccessLogMiddleware(make_app()))
    assert float(LINE.match(access_lines()[0])["rt"]) >= 0


@pytest.mark.parametrize("skip_env, path, logged", [
    (None, "/health", False),
    (None, "/healthz", False),
    (None, "/healthcheck", True),
    ("/ping, /status", "/ping", False),
    ("/ping, /status", "/health", True),
])
async def test_access_log_skip_paths(access_lines, monkeypatch, skip_env, path, logged):
    if skip_env is not None:
        monkeypatch.setenv("ACCESS_LOG_SKIP", skip_env)
    sent = await request(AccessLogMiddleware(make_app()), path=path)
    assert sent[0]["status"] == 200
    assert (len(access_lines()) == 1) == logged


async def test_access_log_escapes_quotes_and_newlines(access_lines):
    headers = [(b"user-agent", b'evil"\n1.2.3.4 - - [x] "GET /admin')]
    await request(AccessLogMiddleware(make_app()), headers=headers)
    (line,) = access_lines()
    assert "\n" not in line and LINE.match(line)["ua"] == 'evil\\"\\x0a1.2.3.4 - - [x] \\"GET /admin'


async def test_access_log_unhandled_exception_logged_as_500(access_lines):
    with pytest.raises(RuntimeError):
        await request(AccessLogMiddleware(make_app(fail=True)))
    assert LINE.match(access_lines()[0])["status"] == "500"


async def test_access_log_ignores_non_http_scopes(access_lines):
    async def lifespan_app(scope, receive, send):
        pass
    await request(AccessLogMiddleware(lifespan_app), scope_type="lifespan")
    assert access_lines() == []


def test_access_log_service_defaults_to_hostname(monkeypatch):
    monkeypatch.delenv("SERVICE_NAME", raising=False)
    monkeypatch.setattr(access_log.socket, "gethostname", lambda: "container-1")
    assert AccessLogMiddleware(make_app()).service == "container-1"


# ------------------------------------------------------------ setup_logging()

@pytest.fixture
def restore_handlers():
    """setup_logging() adds handlers to process-wide loggers; remove them after each test."""
    loggers = [logging.getLogger(), logging.getLogger("access")]
    before = [list(lg.handlers) for lg in loggers]
    yield
    for lg, old in zip(loggers, before):
        for handler in [h for h in lg.handlers if h not in old]:
            lg.removeHandler(handler)
            handler.close()


def file_handlers():
    # WatchedFileHandler only: pytest attaches a FileHandler of its own to the root logger
    return [h for lg in (logging.getLogger(), logging.getLogger("access")) for h in lg.handlers
            if isinstance(h, logging.handlers.WatchedFileHandler)]


def test_setup_logging_writes_log_files(tmp_path, monkeypatch, restore_handlers):
    monkeypatch.setenv("LOG_DIR", str(tmp_path))
    utils.setup_logging()
    logging.getLogger("access").info("ACCESS LINE")
    logging.getLogger("some.module").info("info line")
    logging.getLogger("some.module").warning("warning line")
    for handler in file_handlers():
        handler.flush()

    assert (tmp_path / "access.log").read_text() == "ACCESS LINE\n"
    error_log = (tmp_path / "error.log").read_text()
    assert re.fullmatch(r"\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d{3} \[WARNING\] some\.module: warning line\n", error_log)


def test_setup_logging_uses_watched_file_handlers(tmp_path, monkeypatch, restore_handlers):
    monkeypatch.setenv("LOG_DIR", str(tmp_path))
    utils.setup_logging()
    assert sorted(h.baseFilename for h in file_handlers()) == [str(tmp_path / "access.log"),
                                                               str(tmp_path / "error.log")]


@pytest.mark.parametrize("make_log_dir", [
    lambda tmp: tmp / "missing",
    lambda tmp: (tmp / "a-file").write_text("") and tmp / "a-file",
], ids=["missing directory", "path is a file"])
def test_setup_logging_unusable_log_dir_only_warns(tmp_path, monkeypatch, caplog, restore_handlers, make_log_dir):
    monkeypatch.setenv("LOG_DIR", str(make_log_dir(tmp_path)))
    utils.setup_logging()
    assert file_handlers() == []
    assert any(r.levelno == logging.WARNING and "Log files disabled" in r.getMessage() for r in caplog.records)


def test_setup_logging_without_log_dir_adds_no_files(monkeypatch, restore_handlers):
    monkeypatch.delenv("LOG_DIR", raising=False)
    utils.setup_logging()
    assert file_handlers() == []
