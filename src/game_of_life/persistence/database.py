"""Database connection and batched commit handling."""

import json
from pathlib import Path
from typing import Any, Generator

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session, sessionmaker
from typeguard import typechecked

from game_of_life.config import SimulationConfig
from game_of_life.persistence.models import Base, SimulationRun, IterationRecord


@typechecked
def get_engine(db_path: Path) -> Engine:
    """Create a SQLAlchemy engine for the given SQLite path."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{db_path}")


@typechecked
def init_db(engine: Engine) -> None:
    """Create all tables in the database."""
    Base.metadata.create_all(engine)


@typechecked
def create_run_record(session: Session, config: SimulationConfig, rows: int, cols: int, initial_source: str = "initial.pkl") -> SimulationRun:
    """Create and return a new SimulationRun record."""
    from dataclasses import asdict
    
    # Simple JSON serialization of the config
    config_dict = asdict(config)
    # Convert enums and paths to string for JSON
    config_dict["boundary_mode"] = config_dict["boundary_mode"].name
    config_dict["db_path"] = str(config_dict["db_path"])
    
    run = SimulationRun(
        grid_rows=rows,
        grid_cols=cols,
        boundary_mode=config.boundary_mode.name,
        initial_source=initial_source,
        config_json=json.dumps(config_dict),
    )
    session.add(run)
    session.commit()
    return run


class BatchedCommitter:
    """Helper to commit records in batches to avoid SQLite performance traps."""
    
    def __init__(self, session: Session, batch_size: int = 25):
        self.session = session
        self.batch_size = batch_size
        self._uncommitted_count = 0

    def add(self, record: Base) -> None:
        """Add a record to the session and commit if the batch size is reached."""
        self.session.add(record)
        self._uncommitted_count += 1
        if self._uncommitted_count >= self.batch_size:
            self.commit()

    def commit(self) -> None:
        """Force a commit of any pending records."""
        if self._uncommitted_count > 0:
            self.session.commit()
            self._uncommitted_count = 0
