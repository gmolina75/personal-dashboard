"""SQLAlchemy model for dashboard records."""

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Text, JSON


class Base(DeclarativeBase):
    """Base declarative class for SQLAlchemy models."""
    pass


class RecordModel(Base):
    """Model for storing dashboard records from various sources."""
    __tablename__ = "records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source: Mapped[str] = mapped_column(String(32), index=True)  # gmail, calendar, tasks, drive
    type: Mapped[str] = mapped_column(String(32), index=True)   # message, event, task, document
    title: Mapped[str] = mapped_column(String(255))
    snippet: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str] = mapped_column(String(512), default="")
    ts_start: Mapped[int] = mapped_column(Integer, default=0, index=True)
    ts_end: Mapped[int] = mapped_column(Integer, default=0)
    meta_json: Mapped[dict] = mapped_column(JSON, default=dict)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[int] = mapped_column(Integer, index=True)