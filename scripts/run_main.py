#  Copyright (c) 2026. Programacion Cientifica, DISC, Antofagasta, Chile.

import logging

from benchmarking import benchmark  # ty:ignore[unresolved-import]
from logger import configure_logging  # ty:ignore[unresolved-import]

print("Testing")

def main():
    """The main function"""
    value = 10.1
    # debug: mensaje para conocer los internals del modelo
    log.debug(f"debug message -> value={value}.")

    # info: mensaje informativo
    log.info(f"info message -> value={value}.")

    # warning: mensaje de un error, pero que puede ser superado
    log.warning(f"warning message -> value={value}.")

    # error: ocurrio un error en el codigo
    log.error(f"error message -> value={value}.")

    # fatal: ocurrio un error que no permite continuar
    log.fatal(f"fatal message -> value={value}.")
    pass


# Call the main function
if __name__ == '__main__':
    # configure the logging
    configure_logging(logging.DEBUG)
    # get the main logger
    log = logging.getLogger(__name__)
    # measure time
    with benchmark("main", log):
        main()
