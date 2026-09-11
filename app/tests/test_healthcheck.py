"""Tests for the container health check."""
from sqlalchemy import create_engine

import healthcheck


def test_healthcheck_ok_when_database_answers():
    engine = create_engine("sqlite:///:memory:")
    assert healthcheck.check(engine) == 0


def test_healthcheck_fails_when_database_unreachable():
    engine = create_engine("postgresql+psycopg://nobody:nothing@127.0.0.1:1/none")
    assert healthcheck.check(engine) == 1


def test_normalise_database_url_forces_psycopg3():
    import database
    assert database.normalise_database_url("postgresql://u:p@db/x") == "postgresql+psycopg://u:p@db/x"
    assert database.normalise_database_url("postgresql+psycopg://u:p@db/x") == "postgresql+psycopg://u:p@db/x"
    assert database.normalise_database_url("sqlite:///:memory:") == "sqlite:///:memory:"
