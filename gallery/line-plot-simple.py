#!/usr/bin/env python3

import matplotlib.pyplot as plt

from mpl_typst import rc_context

with rc_context():
    fig, ax = plt.subplots()
    ax.plot([i ** 2 for i in range(10)], '-..', label=r'$x^2$')
    ax.legend()
    ax.set_xlabel(r'$x$')
    ax.set_ylabel(r'$f(x)$')
    # fig.savefig('line-plot-simple.typ')
    fig.savefig('line-plot-simple.png')
