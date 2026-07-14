import logging
from pathlib import Path

import instructor
from pydantic import BaseModel, Field

from benchmarking import benchmark
from logger import configure_logging

log = logging.getLogger(__name__)


class Ingredient(BaseModel):
    name: str = Field(description="Ingredient name")
    description: str = Field(description="Ingredient description")
    unit: str = Field(description="Ingredient unit")
    value: float = Field(description="Ingredient value")


class Recipe(BaseModel):
    name: str = Field(description="Recipe name")
    ingredients: list[Ingredient] = Field(description="Recipe ingredients")


def main() -> None:
    # client to use llm
    client = instructor.from_provider(
        "deepseek/deepseek-chat",
        base_url="https://api.deepseek.com",
    )

    description = "6 presas de pollo, pueden adaptar a gusto de los comensales, pero lo más común sería 3 trutos largos y 3 cortos, 1 cebollas picada en cubos. 3 zanahorias, pueden ser ralladas o picadas en trozos grandes. 2 choclos con coronta, cortado en 6 trozos total. ½ kilo de zapallo amarillo cortado en 6 trozos iguales. 6 papas medianas peladas. una rama de apio, perejil y orégano, en ramito si desea retirarla después. 3 dientes de ajo pelados. 1 cucharadita de comino.pimentón en trozos (optativo). 2 puñados de porotos verdes o arvejas (optativo). 3 puñados o ¼ taza de arroz (lavado)"
    recipe = client.create(
        messages=[
            {"role": "user", "content": description},
        ],
        response_model=Recipe,
    )
    log.debug(f"recipe: {recipe.model_dump_json(indent=4)}")


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
