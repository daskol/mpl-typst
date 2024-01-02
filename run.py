#!/usr/bin/env python3

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backend_bases import register_backend

import backend_typst

with mpl.rc_context({'backend': 'module://backend_typst'}):
    print('backend:    ', mpl.get_backend())
    print('interactive:', mpl.is_interactive())

    fig, ax = plt.subplots()
    ax.plot([i ** 2 for i in range(10)], '-.o', label=r'$x^2$')
    ax.legend()
    ax.set_xlabel(r'$x$')
    ax.set_ylabel(r'$f(x)$')
    fig.savefig('out.typ')
