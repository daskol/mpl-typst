#!/usr/bin/env python3

import matplotlib.pyplot as plt

from mpl_typst import rc_context

DATA = [[1, 2, 3, 4, 5], [2, 3, 4, 5, 6], [3, 4, 5, 6, 7]]

with rc_context():
    fig, ax = plt.subplots(figsize=(6.5, 3.0), layout='constrained')
    labels = ['Data 1', 'Data 2', 'Data 3']
    colors = ['black', '#CC79A7', '#56B4E9']
    _counts, _bins, patches = ax.hist(
        DATA, bins=5, color=colors, edgecolor='black')  # type: ignore

    for patch in patches[-1]:  # type: ignore[index]
        patch.set_hatch('//')

    ax.set_xlabel('Value')
    ax.set_ylabel('Count')
    ax.set_title('Histogram with Hatch Patterns')
    ax.legend(labels)

    fig.savefig('hist-hatched.typ')
    fig.savefig('hist-hatched.pdf')
    fig.savefig('hist-hatched.png')
    fig.savefig('hist-hatched.svg')
