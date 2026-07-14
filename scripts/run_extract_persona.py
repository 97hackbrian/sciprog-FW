import logging
from pathlib import Path

import instructor
from pydantic import BaseModel, field_validator

from benchmarking import benchmark
from logger import configure_logging

log = logging.getLogger(__name__)


class Persona(BaseModel):
    name: str
    age: int

    @field_validator("name")
    @classmethod
    def must_have_space(cls, v: str) -> str:
        if " " not in v:
            raise ValueError(f"Invalid persona name: {v}")
        return v

    @field_validator("age")
    @classmethod
    def reasonable_age(cls, v: int) -> int:
        if v <= 0 or v > 120:
            raise ValueError(f"Invalid persona age: {v}")
        return v


def main() -> None:
    # client to use llm
    client = instructor.from_provider(
        "deepseek/deepseek-chat",
        base_url="https://api.deepseek.com",
    )

    # request the model
    persona = client.create(
        messages=[
            {"role": "user", "content": "Extract: John Lucas is 450 years old"},
        ],
        response_model=Persona,
    )

    log.debug(f"persona: {persona}")


# call the main function
if __name__ == '__main__':
    configure_logging(logging.DEBUG)

    root_dir = Path(__file__).resolve().parent.parent
    log.debug(f"root_dir: {root_dir}")

    output_dir = root_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    log.debug(f"output_dir: {output_dir}")

    with benchmark("main", log):
        log.info("️🏎️ starting ..")
        main()
