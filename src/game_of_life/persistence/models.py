"""SQLAlchemy ORM models for Game of Life persistence."""

from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models."""
    pass


class SimulationRun(Base):
    """Record of a complete simulation session."""
    __tablename__ = "simulation_run"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(default=datetime.now)
    grid_rows: Mapped[int]
    grid_cols: Mapped[int]
    boundary_mode: Mapped[str] = mapped_column(String(50))
    initial_source: Mapped[str] = mapped_column(String(255))
    config_json: Mapped[str] = mapped_column(String)  # JSON serialized config snapshot


class IterationRecord(Base):
    """Record of a single generation's statistics."""
    __tablename__ = "iteration_record"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("simulation_run.id", ondelete="CASCADE"))
    iteration_number: Mapped[int] = mapped_column(Integer, index=True)
    live_cells: Mapped[int]
    dead_cells: Mapped[int]
    execution_time_ms: Mapped[float]
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
