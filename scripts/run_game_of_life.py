"""Command-line entrypoint for the Game of Life."""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session

from libs.config import SimulationConfig
from libs.core.engine import SimulationEngine
from libs.gui.app import GameOfLifeApp
from libs.logging_config import configure_logging
from libs.persistence.database import (
    BatchedCommitter,
    create_run_record,
    get_engine,
    init_db,
)
from libs.persistence.loader import load_initial_state
from libs.persistence.models import IterationRecord

log = logging.getLogger(__name__)


def run_headless(engine: SimulationEngine, db_session: Session, run_id: int) -> None:
    """Run the simulation without the GUI, saving to database."""
    log.info("Starting headless simulation loop...")
    committer = BatchedCommitter(db_session, batch_size=25)

    try:
        while True:
            result = engine.step()

            record = IterationRecord(
                run_id=run_id,
                iteration_number=result.iteration,
                live_cells=result.live_cells,
                dead_cells=result.dead_cells,
                execution_time_ms=result.execution_time_ms,
            )
            committer.add(record)

            if result.iteration % 100 == 0:
                log.info(f"Iteration {result.iteration}: {result.live_cells} live cells")

            if result.is_stable:
                log.info(f"Simulation stopped at iteration {result.iteration} due to stability.")
                break

    except KeyboardInterrupt:
        log.info("Simulation stopped by user.")
    finally:
        committer.commit()
        log.info("Database records committed. Exiting.")


def main() -> None:
    """Entry point for the Game of Life CLI."""
    parser = argparse.ArgumentParser(description="Conway's Game of Life")
    parser.add_argument(
        "--initial",
        type=Path,
        default=Path("data/initial.pkl"),
        help="Path to initial state pickle",
    )
    parser.add_argument("--config", type=Path, default=None, help="Path to config yaml")
    parser.add_argument("--headless", action="store_true", help="Run without GUI")
    parser.add_argument(
        "--backend",
        type=str,
        choices=["auto", "cpu", "gpu"],
        default=None,
        help="Compute backend to use",
    )
    args = parser.parse_args()

    # Load configuration
    config = SimulationConfig.load(args.config)
    if args.backend:
        from libs.config import ComputeBackend

        config.backend = ComputeBackend[args.backend.upper()]

    # Configure logging
    log_dir = Path("logs")
    configure_logging(level=config.log_level, log_dir=log_dir)

    log.info("Initializing Game of Life...")

    # Load initial state
    try:
        initial_state = load_initial_state(args.initial)
    except Exception as e:
        log.error(f"Failed to load initial state: {e}")
        return

    # Setup database
    db_engine = get_engine(config.db_path)
    init_db(db_engine)

    # Create simulation engine
    sim_engine = SimulationEngine(config=config, initial=initial_state)

    # We need a db session to persist data
    with Session(db_engine) as session:
        # Create run record
        run_record = create_run_record(
            session, config, initial_state.shape[0], initial_state.shape[1], str(args.initial)
        )
        log.info(f"Created simulation run record {run_record.id}")

        if args.headless:
            run_headless(sim_engine, session, run_record.id)
        else:
            log.info("Starting GUI...")
            app = GameOfLifeApp(engine=sim_engine, config=config, initial_state=initial_state)

            # We persist execution records in GUI mode via a monkeypatch.
            committer = BatchedCommitter(session, batch_size=25)

            def persist_result(result: Any) -> None:
                record = IterationRecord(
                    run_id=run_record.id,
                    iteration_number=result.iteration,
                    live_cells=result.live_cells,
                    dead_cells=result.dead_cells,
                    execution_time_ms=result.execution_time_ms,
                )
                committer.add(record)

            # Monkeypatch the engine's step temporarily to hook it
            orig_step = sim_engine.step

            def hooked_step() -> Any:
                res = orig_step()
                persist_result(res)
                return res

            sim_engine.step = hooked_step  # type: ignore[method-assign]

            app.run()
            committer.commit()
            log.info("GUI closed. Database records committed.")


if __name__ == "__main__":
    main()
