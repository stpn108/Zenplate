"""DATABASE_URL: plain PostgreSQL URLs must select the installed psycopg 3 driver."""
import pytest
from sqlalchemy.engine import make_url

from database import normalize_database_url


@pytest.mark.parametrize("url,expected", [
    ("postgresql://u:p@db/x", "postgresql+psycopg://u:p@db/x"),
    ("postgres://u:p@db/x", "postgresql+psycopg://u:p@db/x"),
    ("postgresql+psycopg://u:p@db/x", "postgresql+psycopg://u:p@db/x"),
    ("sqlite:///:memory:", "sqlite:///:memory:"),
])
def test_normalize_database_url(url, expected):
    assert normalize_database_url(url) == expected


def test_normalized_postgres_url_resolves_to_psycopg_dialect():
    # Bug: "postgresql://" made SQLAlchemy import psycopg2, which is not installed.
    dialect = make_url(normalize_database_url("postgresql://u:p@db/x")).get_dialect()
    assert dialect.driver == "psycopg"
