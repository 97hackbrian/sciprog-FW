#  Copyright (c) 2026. Programacion Cientifica, DISC, Antofagasta, Chile.
import logging
from pathlib import Path

import pymupdf4llm

from benchmarking import benchmark
from logger import configure_logging


def main():
    # locate the root dir of the project
    root_dir = Path(__file__).parent.parent
    log.debug(f"root_dir: {root_dir}")

    # input file (pdf)
    input_file = root_dir / "data" / "uso-de-python-para-la-modelacion-y-determinacion-de-vida-util-de-matrices-alimentarias.pdf"
    log.debug(f"input_file: {input_file}")

    # output file (markdown)
    output_file = root_dir / "output" / "uso-de-python-para-la-modelacion-y-determinacion-de-vida-util-de-matrices-alimentarias.md"
    log.debug(f"output_file: {output_file}")

    # read the input file into markdown
    with benchmark("convert pdf2md", log):
        md = pymupdf4llm.to_markdown(input_file)

    # write the markdown data
    with benchmark("writting", log):
        output_file.write_text(md, encoding="utf-8")

# Call the main function
if __name__ == '__main__':
    # configure the logging
    configure_logging(logging.DEBUG)
    # get the main logger
    log = logging.getLogger(__name__)
    # measure time
    with benchmark("main", log):
        log.info("⬇️🏎️ starting ..")
        main()
        log.info("⬆️🏁 done.")
