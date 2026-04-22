#  Copyright (c) 2026. Programacion Cientifica, DISC, Antofagasta, Chile.
import logging
from logging import Logger
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

    # the file don't exists
    if not input_file.exists():
        log.error(f"input file not found: {input_file}")
        raise FileNotFoundError(f"input file not found: {input_file}")

    # output file (markdown)
    output_file = root_dir / "output" / "uso-de-python-para-la-modelacion-y-determinacion-de-vida-util-de-matrices-alimentarias.md"
    log.debug(f"output_file: {output_file}")

    # create the directory if don't exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # read the input file into markdown
    with benchmark("pdf2md", log):
        log.debug("converting pdf to markdown ..")
        md = pymupdf4llm.to_markdown(input_file)

    # write the markdown data
    with benchmark("write", log):
        log.debug(f"writing {len(md)} chars ..")
        output_file.write_text(md, encoding="utf-8")

# Call the main function
if __name__ == '__main__':
    # configure the logging
    configure_logging(logging.DEBUG)
    # get the main logger
    log: Logger = logging.getLogger(__name__)
    # measure time
    with benchmark("main", log):
        log.info("️🏎️ starting ..")
        main()
        log.info("️🏁 done.")
