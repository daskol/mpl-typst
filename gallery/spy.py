#!/usr/bin/env python3

import matplotlib.pyplot as plt
import numpy as np

from mpl_typst import rc_context

rng = np.random.default_rng(42)
mat = rng.integers(0, 2, size=(8, 16))

with rc_context():
    fig, ax = plt.subplots(figsize=(3.25, 2.01), dpi=288)
    ax.spy(mat)
    ax.set_xlabel('Tokens')
    ax.set_ylabel('Experts')
    fig.savefig('spy.typ')
    fig.savefig('spy.pdf')
    fig.savefig('spy.png')
    fig.savefig('spy.svg')
