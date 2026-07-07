#  Copyright (c) 2026. Programacion Cientifica, DISC, Antofagasta, Chile.
import logging
from pathlib import Path

from sqlalchemy import String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

from benchmarking import benchmark
from logger import configure_logging


# the base class
class Base(DeclarativeBase):
    pass


# the user class
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    age: Mapped[int] = mapped_column(nullable=False)

    def __repr__(self) -> str:
        return f"User(id={self.id},name={self.name},email={self.email},age={self.age})"


def main() -> None:
    # create the engine
    engine = create_engine(f"sqlite:///{output_dir / 'users.db'}", echo=False)

    # delete all the tables
    Base.metadata.drop_all(engine)

    # create all the tables
    Base.metadata.create_all(engine)

    # the users to save
    users = [
        User(name="John", email="john@afta.cl", age=21),
        User(name="Andrea", email="andrea@afta.cl", age=30),
        User(name="Julia", email="julia@afta.cl", age=55),
    ]

    # the session
    session = Session(engine)

    # add all the users to the session
    session.add_all(users)

    # materialize the insert
    session.commit()

    # query the database
    for user in session.query(User).all():
        log.debug(f"user: {user}")

    # close the current session
    session.close()

    # close the database engine
    engine.dispose()


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
