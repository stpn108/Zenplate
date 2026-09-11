"""
Main application entrypoint.

Replace this with your actual application logic.
"""
import os
import logging
import threading
from database import migrate_schema
from utils import setup_logging

setup_logging()
log = logging.getLogger(__name__)


def main():
    # Create tables and apply pending migrations (idempotent, lock-protected)
    migrate_schema()
    log.info(
        "App v%s (%s) started",
        os.getenv("APP_VERSION", "0.0"),
        os.getenv("GIT_COMMIT", "unknown"),
    )

    # --- Your application logic here ---
    log.info("Ready.")
    # Placeholder: keep the process alive so the container stays up and the
    # health check can pass. Replace with your app's run loop / server.
    threading.Event().wait()


if __name__ == "__main__":
    main()
