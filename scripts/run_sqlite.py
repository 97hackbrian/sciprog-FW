#  Copyright (c) 2026. Programacion Cientifica, DISC, Antofagasta, Chile.
import logging
import sqlite3
import sys
from pathlib import Path

# ensure libs/ is on the path
_script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(_script_dir.parent / "libs"))

from benchmarking import benchmark  # ty:ignore[unresolved-import]
from logger import configure_logging  # ty:ignore[unresolved-import]


def main() -> None:
    # create a connection to sqlite
    db = sqlite3.connect(output_dir / "database.db")

    # the cursor to connect
    cur = db.cursor()

    # create the tables
    cur.execute("""
                CREATE TABLE IF NOT EXISTS users
                (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    age INTEGER NOT NULL
                )
                """)

    # the list of users to create
    users = [
        ("John", "john@antofagasta.cl", 21),
        ("Andrea", "andrea@antofagasta.cl", 30),
        ("Julia", "julia@antofagasta.cl", 55),
    ]

    # insert the whole list of users into the table users
    cur.executemany("INSERT INTO users (name, email, age) VALUES (?, ?, ?)", users)

    # materialize the insert
    db.commit()

    log.debug(f"Created {cur.rowcount} users in the database")

    # query the database
    for row in cur.execute("SELECT * FROM users"):
        log.debug(f"Row: {row}")

    # update the age of john
    age = 18
    email = 'john@antofagasta.cl'
    cur.execute(f"UPDATE users SET AGE = ? WHERE EMAIL = ?", (age, email))

    # close the database
    db.close()



# call the main function
if __name__ == '__main__':
    configure_logging(logging.DEBUG)
    log = logging.getLogger(__name__)

    root_dir = Path(__file__).resolve().parent.parent
    log.debug(f"root_dir: {root_dir}")

    output_dir = root_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    log.debug(f"output_dir: {output_dir}")

    with benchmark("main", log):
        log.info("starting ..")
        main()
        log.info("done.")
