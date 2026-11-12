"""
Utility helpers: timezone, datetime, formatting, logging.

IMPORTANT (see CLAUDE.md):
  - Always use now_utc() for timestamps, local_today() for date logic.
  - NEVER use datetime.now() directly.
  - Use setup_logging() once at startup. Get per-module loggers via logging.getLogger(__name__).
"""
import os
import logging
import logging.handlers
import datetime as dt
from dateutil import tz
from typing import Optional

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
LOCAL_TZ = tz.gettz(os.getenv("TZ", "Europe/Berlin"))
DEFAULT_TZ_NAME = "Europe/Berlin"


# ---------------------------------------------------------
# LOGGING
# ---------------------------------------------------------
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def setup_logging():
    """
    Configure root logger from LOG_LEVEL env var. Call once at startup.

    With LOG_DIR set (T-015), WARNING and above also go to LOG_DIR/error.log and the
    "access" logger (access_log.AccessLogMiddleware) also to LOG_DIR/access.log. Both keep
    going to stdout. WatchedFileHandler reopens a file after logrotate moved it.
    A LOG_DIR that cannot be written only logs a warning; the app starts without the files.
    """
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format=LOG_FORMAT,
    )
    access = logging.getLogger("access")
    access.setLevel(logging.INFO)

    log_dir = os.getenv("LOG_DIR")
    if not log_dir:
        return
    handlers = []
    try:
        for name in ("error.log", "access.log"):
            handlers.append(logging.handlers.WatchedFileHandler(os.path.join(log_dir, name), encoding="utf-8"))
    except OSError as exc:
        for handler in handlers:
            handler.close()
        logging.getLogger(__name__).warning(
            "Log files disabled: cannot write to LOG_DIR=%s (%s). Logging to stdout only.", log_dir, exc
        )
        return
    error_handler, access_handler = handlers
    error_handler.setLevel(logging.WARNING)
    error_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    access_handler.setFormatter(logging.Formatter("%(message)s"))
    logging.getLogger().addHandler(error_handler)
    access.addHandler(access_handler)


# ---------------------------------------------------------
# TIMEZONE HELPERS
# ---------------------------------------------------------
def get_tz(user_tz: Optional[str] = None) -> dt.tzinfo:
    """Returns a timezone object. Falls back to LOCAL_TZ if invalid."""
    if user_tz:
        parsed = tz.gettz(user_tz)
        if parsed:
            return parsed
    return LOCAL_TZ


def now_utc() -> dt.datetime:
    """Current time in UTC (always timezone-aware)."""
    return dt.datetime.now(dt.timezone.utc)


def local_today(user_tz: Optional[str] = None) -> dt.date:
    """
    Today's date in the specified timezone.
    Day boundary is 04:00 (late-night entries count as previous day).
    """
    user_tzinfo = get_tz(user_tz)
    now = now_utc().astimezone(user_tzinfo)
    if now.hour < 4:
        return (now - dt.timedelta(days=1)).date()
    return now.date()


def today_str(user_tz: Optional[str] = None) -> str:
    """Today's date as ISO string (YYYY-MM-DD)."""
    return local_today(user_tz).isoformat()


def yesterday_str(user_tz: Optional[str] = None) -> str:
    """Yesterday's date as ISO string."""
    return (local_today(user_tz) - dt.timedelta(days=1)).isoformat()
