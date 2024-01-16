#!/usr/bin/env python3

import matplotlib.pyplot as plt

from mpl_typst import rc_context
from mpl_typst.aux import LogFormatterSciNotation

with rc_context({
        'text.parse_math': False,
        'text.usetex': False,
        'axes.formatter.use_mathtext': False,
}):
    fig, ax = plt.subplots(figsize=(3.25, 2.01), layout='constrained')
    ax: plt.Axes = ax
    ax.semilogy([i ** 2 for i in range(10)], '-..', label=r'$x^2$')
    ax.legend()
    ax.set_xlabel(r'$x$')
    ax.set_ylabel(r'$f(x)$')
    ax.yaxis.set_major_formatter(LogFormatterSciNotation())
    fig.savefig('line-plot-simple.pdf')
    fig.savefig('line-plot-simple.png')
    fig.savefig('line-plot-simple.svg')
    fig.savefig('line-plot-simple.typ')
