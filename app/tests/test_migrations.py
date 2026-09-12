"""Tests for the schema migration runner."""
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

import database


@pytest.fixture
def memory_engine():
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def _applied_versions(engine):
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT version FROM schema_migrations")).fetchall()
    return {r[0] for r in rows}


def test_migrate_schema_creates_tables_and_tracking_table(memory_engine, monkeypatch):
    monkeypatch.setattr(database, "MIGRATIONS", [])

    database.migrate_schema(memory_engine)

    with memory_engine.connect() as conn:
        conn.execute(text("SELECT id FROM example_items"))
    assert _applied_versions(memory_engine) == set()


def test_migrate_schema_applies_each_migration_once(memory_engine, monkeypatch):
    calls = []

    def _migrate_001(conn):
        calls.append("001")
        conn.execute(text("ALTER TABLE example_items ADD COLUMN priority INTEGER DEFAULT 0"))

    def _migrate_002(conn):
        calls.append("002")

    monkeypatch.setattr(database, "MIGRATIONS", [
        ("001_priority", _migrate_001),
        ("002_noop", _migrate_002),
    ])

    database.migrate_schema(memory_engine)
    database.migrate_schema(memory_engine)  # second run must be a no-op

    assert calls == ["001", "002"]
    assert _applied_versions(memory_engine) == {"001_priority", "002_noop"}
    with memory_engine.connect() as conn:
        conn.execute(text("SELECT priority FROM example_items"))


def test_migrate_schema_skips_already_applied_and_runs_new_ones(memory_engine, monkeypatch):
    calls = []
    monkeypatch.setattr(database, "MIGRATIONS", [
        ("001_first", lambda conn: calls.append("001")),
    ])
    database.migrate_schema(memory_engine)

    monkeypatch.setattr(database, "MIGRATIONS", [
        ("001_first", lambda conn: calls.append("001")),
        ("002_second", lambda conn: calls.append("002")),
    ])
    database.migrate_schema(memory_engine)

    assert calls == ["001", "002"]


def test_failed_migration_is_rolled_back_and_not_recorded(memory_engine, monkeypatch):
    def _broken(conn):
        raise RuntimeError("boom")

    monkeypatch.setattr(database, "MIGRATIONS", [("001_broken", _broken)])

    with pytest.raises(RuntimeError):
        database.migrate_schema(memory_engine)

    monkeypatch.setattr(database, "MIGRATIONS", [])
    database.migrate_schema(memory_engine)
    assert "001_broken" not in _applied_versions(memory_engine)


@pytest.mark.parametrize("url, expected", [
    ("postgresql://zenplate:pw@db/zenplate", "postgresql+psycopg://zenplate:pw@db/zenplate"),
    ("postgresql+psycopg://zenplate:pw@db/zenplate", "postgresql+psycopg://zenplate:pw@db/zenplate"),
    ("sqlite:///:memory:", "sqlite:///:memory:"),
])
def test_database_url_uses_psycopg3_driver(url, expected):
    # Bug: DATABASE_URL=postgresql://... made SQLAlchemy import psycopg2, which is not installed.
    assert database._normalise_url(url) == expected
