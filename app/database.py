"""
SQLAlchemy models and schema migrations.

Rules (see CLAUDE.md):
  - New table:  Add Model class here -> auto-created via Base.metadata.create_all()
  - New column: Add to Model AND add idempotent migration in migrate_schema()
  - Always use IF NOT EXISTS / IF EXISTS in migrations
"""
import os
import datetime as dt
from typing import Optional
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime,
    Text, Boolean, func, text as sqltext,
)
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, Session

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# EXAMPLE MODEL — replace with your own
# ---------------------------------------------------------------------------
class ExampleItem(Base):
    __tablename__ = "example_items"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ---------------------------------------------------------------------------
# SCHEMA MIGRATIONS (idempotent)
# ---------------------------------------------------------------------------
def migrate_schema():
    """
    Run idempotent ALTER TABLE statements for columns added after initial
    table creation. Called once at startup.

    Example:
        conn.execute(sqltext(
            "ALTER TABLE IF EXISTS example_items "
            "ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 0;"
        ))
    """
    with engine.connect() as conn:
        # Add migrations here
        conn.commit()
