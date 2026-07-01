"""Tests for the persistence layer."""

import pickle
import sqlite3
from pathlib import Path

import numpy as np
import pytest
from sqlalchemy.orm import Session

from libs.config import SimulationConfig
from libs.persistence.database import BatchedCommitter, create_run_record, get_engine, init_db
from libs.persistence.loader import load_initial_state
from libs.persistence.models import IterationRecord


def test_loader_raw_ndarray(tmp_path: Path) -> None:
    """Test loading a raw ndarray from a pickle."""
    grid = np.zeros((10, 10), dtype=np.uint8)
    grid[5, 5] = 1

    pkl_path = tmp_path / "raw.pkl"
    with open(pkl_path, "wb") as f:
        pickle.dump(grid, f)

    loaded = load_initial_state(pkl_path)
    np.testing.assert_array_equal(grid, loaded)


def test_loader_dict_wrapped(tmp_path: Path) -> None:
    """Test loading a dict-wrapped ndarray from a pickle."""
    grid = np.zeros((10, 10), dtype=np.uint8)
    grid[3, 3] = 1

    pkl_path = tmp_path / "dict.pkl"
    with open(pkl_path, "wb") as f:
        pickle.dump({"board": grid}, f)

    loaded = load_initial_state(pkl_path)
    np.testing.assert_array_equal(grid, loaded)


def test_loader_invalid_payload(tmp_path: Path) -> None:
    """Test loader raises ValueError on invalid payload."""
    pkl_path = tmp_path / "invalid.pkl"
    with open(pkl_path, "wb") as f:
        pickle.dump([1, 2, 3], f)  # list instead of array or dict

    with pytest.raises(ValueError, match="Invalid pickle payload"):
        load_initial_state(pkl_path)


def test_database_and_batched_commits(tmp_path: Path) -> None:
    """Test that a short run produces the expected records correctly via batched commit."""
    db_path = tmp_path / "test.sqlite"
    engine = get_engine(db_path)
    init_db(engine)

    config = SimulationConfig()

    with Session(engine) as session:
        run = create_run_record(session, config, rows=20, cols=20)
        assert run.id == 1

        # Simulate 60 iterations with batch size 25
        committer = BatchedCommitter(session, batch_size=25)

        for i in range(60):
            record = IterationRecord(
                run_id=run.id,
                iteration_number=i,
                live_cells=10 + i,
                dead_cells=390 - i,
                execution_time_ms=1.5,
            )
            committer.add(record)

        # At this point, 2 batches (50) should be committed, and 10 pending
        # Let's commit the rest
        committer.commit()

    # Verify row count directly via sqlite3 to ensure they actually hit the disk
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM iteration_record")
    count = cursor.fetchone()[0]

    assert count == 60, f"Expected 60 iteration records, got {count}"
