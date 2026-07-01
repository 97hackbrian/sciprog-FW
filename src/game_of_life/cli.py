"""Command-line entrypoint for the Game of Life."""

import argparse
from pathlib import Path

from sqlalchemy.orm import Session

from game_of_life.config import SimulationConfig
from game_of_life.core.engine import SimulationEngine
from game_of_life.gui.app import GameOfLifeApp
from game_of_life.logging_config import configure_logging
from game_of_life.persistence.database import BatchedCommitter, create_run_record, get_engine, init_db
from game_of_life.persistence.loader import load_initial_state
from game_of_life.persistence.models import IterationRecord

import logging
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
    parser = argparse.ArgumentParser(description="Conway's Game of Life")
    parser.add_argument("--initial", type=Path, default=Path("initial.pkl"), help="Path to initial state pickle")
    parser.add_argument("--config", type=Path, default=None, help="Path to config yaml")
    parser.add_argument("--headless", action="store_true", help="Run without GUI")
    args = parser.parse_args()

    # Load configuration
    config = SimulationConfig.load(args.config)
    
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
        run_record = create_run_record(session, config, initial_state.shape[0], initial_state.shape[1], str(args.initial))
        log.info(f"Created simulation run record {run_record.id}")
        
        if args.headless:
            run_headless(sim_engine, session, run_record.id)
        else:
            log.info("Starting GUI...")
            app = GameOfLifeApp(engine=sim_engine, config=config, initial_state=initial_state)
            
            # For the GUI, we could inject the committer to save records as it runs,
            # or keep it simple. The spec says "persist to SQLite", 
            # we should persist in GUI mode too if it's meant to record execution.
            # To avoid cluttering the GUI with DB logic, we can wrap the engine step 
            # or hook into it. For now, the prompt implies the headless mode is mainly for DB tests/CI,
            # but usually it's good to persist always. I'll add a simple hook in the loop or 
            # just update run_headless for now. Actually, the spec: "persist to SQLite via SQLAlchemy: iteration number, live cell count...".
            # The app should persist too. Let's patch the app's _do_step.
            
            committer = BatchedCommitter(session, batch_size=25)
            original_do_step = app._do_step
            
            def hooked_do_step():
                original_do_step()
                # The engine just advanced
                result = sim_engine.step() # Wait, original_do_step already calls step()!
                pass # I need to be careful here. I will just edit app.py to accept a committer if needed, or do it cleanly.
                
            # Cleanest way: let's inject a callback into the app or engine.
            # For this MVP, let's just add it to app.py. I'll modify app.py directly via another tool call if needed, 
            # but wait, I can just do it here:
            
            def persist_result(result):
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
            def hooked_step():
                res = orig_step()
                persist_result(res)
                return res
            sim_engine.step = hooked_step
            
            app.run()
            committer.commit()
            log.info("GUI closed. Database records committed.")


if __name__ == "__main__":
    main()
