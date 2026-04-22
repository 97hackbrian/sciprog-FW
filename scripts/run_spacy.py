#  Copyright (c) 2026. Programacion Cientifica, DISC, Antofagasta, Chile.
import logging

import spacy
from prettytable import PrettyTable

from benchmarking import benchmark
from logger import configure_logging


def main():
    text = (
        "La vida util de un alimento se define como el periodo de tiempo en el que "
        "este conserva sus caracteristicas organolepticas y nutricionales que lo "
        "mantienen inocuo. Se desarrollo un programa en Python que llevo a cabo una "
        "simulacion probabilistica de Montecarlo para determinar la vida util de "
        "tomate deshidratado. Los datos necesarios para determinar vida util incluyen "
        "isotermas de GAB, humedad, y otras constantes, los cuales fueron obtenidos "
        "de la literatura."
    )

    with benchmark("nlp", log):
        doc = nlp(text)

    table = PrettyTable()
    table.field_names = ["#", "Token", "Lemma", "POS"]
    table.align = "l"
    table.max_width = 30

    for i, token in enumerate(doc, start=1):
        table.add_row([i, token.text, token.lemma_, token.pos_])

    log.info(f"NPL:\n{table}")

    # log.info(f"tokens founded: {len(doc)}.")
    # for token in doc:
    #    log.debug(f"token: {token.text} -> lemma: {token.lemma_} -> pos: {token.pos_}")


# Call the main function
if __name__ == '__main__':
    # configure the logging
    configure_logging(logging.DEBUG)
    # get the main logger
    log = logging.getLogger(__name__)

    # load spacy
    spacy_model: str = "es_core_news_sm"
    with benchmark(f"load spacy model: {spacy_model}", log):
        nlp = spacy.load(spacy_model)

    # run the main
    with benchmark("main", log):
        log.info("🏎️ starting ..")
        main()
        log.info("️🏁 done.")
