import logging
from pathlib import Path

import numpy as np
import sympy
from scipy.optimize import fsolve
from sympy import symbols, expand, simplify, Eq, solve, diff

from benchmarking import benchmark  # ty:ignore[unresolved-import]
from logger import configure_logging  # ty:ignore[unresolved-import]


def equation(x):
    return np.sin(x) - 0.5

def main() -> None:
    # enable latex
    sympy.init_printing(use_latex=True)

    # define the expression
    x = symbols('x')
    expr = (x + 2) ** 3
    log.debug(f"expr: {expr}")

    # expand
    expand_expr = expand(expr)
    log.debug(f"expand_expr: {expand_expr}")

    # simplify
    simplify_expr = simplify(expand_expr - expr)
    log.debug(f"simplify_expr: {simplify_expr}")

    # equation: x^2 - 4 = 0
    eqq = Eq(x ** 2 - 4, 0)
    eqq_solve = solve(eqq, x)
    log.debug(f"eqq_solve: {eqq_solve}")

    # parabolic movement
    t = symbols('t')
    p = 5 * t ** 3 - 2 * t ** 2 + 4 * t - 1
    log.debug(f"p: {p}")

    velocity = diff(p, t)
    log.debug(f"velocity: {velocity}")

    aceleration = diff(velocity, t)
    log.debug(f"aceleration: {aceleration}")

    # maximizing the profit
    profit = - 2 * x ** 2 + 40 * x - 100
    log.debug(f"profit: {profit}")

    d_profit = diff(profit, x)
    log.debug(f"d_profit: {d_profit}")

    # solve the profit
    max_profit = solve(d_profit, x)
    log.debug(f"max_profit: {max_profit}")

    # system of equations
    y = symbols('y')
    eq1 = Eq(x + y, 10)
    eq2 = Eq(x - y, 4)

    solution = solve((eq1, eq2), (x, y))
    log.debug(f"solution: {solution}")

    # sin(x) = 1/2
    root = fsolve(equation, 0)
    log.debug(f"root: {root}")

    # intersection of a line and a circle
    eq_circle = Eq(x**2 + y**2, 25)
    eq_line = Eq(y, 2 * x + 1)
    solutions = solve((eq_circle, eq_line), (x, y))
    log.debug(f"solutions: {solutions}")

    # system of equations
    a = symbols('a')
    eq1 = Eq(a * x + y, 10)
    eq2 = Eq(x - a * y, 4)
    solution = solve((eq1, eq2), (x, y))
    log.debug(f"solution with a: {solution}")



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
