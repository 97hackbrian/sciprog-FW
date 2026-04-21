#  Copyright (c) 2026. Programacion Cientifica, DISC, Antofagasta, Chile.

import logging

from benchmarking import benchmark
from logger import configure_logging


def main():
    """The main function"""
    valor = 10.1
    # debug: mensaje para conocer los internals del modelo
    log.debug(f"valor = {valor}.")

    # info: mensaje informativo
    log.info(f"valor = {valor}.")

    # warning: mensaje de un error, pero que puede ser superado
    log.warning(f"Warning: valor fuera de escala = {valor}.")

    # error: ocurrio un error en el codigo
    log.error(f"Error: valor no valido= {valor}.")

    # fatal: ocurrio un error que no permite continuar
    log.fatal(f"Fatal: no se puede continuar el computo!")
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
