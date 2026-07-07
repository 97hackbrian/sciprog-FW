import logging
from pathlib import Path

import numpy as np
import sympy
from scipy.optimize import fsolve
from sympy import symbols, expand, simplify, Eq, solve, diff

from benchmarking import benchmark
from logger import configure_logging


def equation(x):
    return np.sin(x) - 0.5

def main() -> None:
    # enable latex
    sympy.init_printing(use_latex=True)

    # define the expression
    a, b, c, d = symbols('a b c d')

    # define the eq
    eq_c = Eq(2 * a, c)
    eq_h = Eq(6 * a, 2 * d)
    eq_o = Eq(a + 2*b, 2 * c + d)

    solutions = solve((eq_c, eq_h, eq_o), (b, c, d))
    log.debug(f"solutions in terms of a: {solutions}")



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
