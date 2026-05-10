#!/usr/bin/env python3

import matplotlib as mpl
import matplotlib.pyplot as plt

from mpl_typst import rc_context

colors = ['C0', 'C1', 'C2']
linestyles = ['-', ':', '-.']
labels = ['text0', 'text1', 'text2']

with rc_context():
    fig, ax = plt.subplots(1, 1)

    handles = [mpl.lines.Line2D([], [], ls=ls, color=color)
               for ls, color in zip(linestyles, colors, strict=True)]

    legend = ax.legend(handles, labels, loc='center', ncol=3,
                       borderaxespad=0.5)

    for text, color in zip(legend.get_texts(), colors, strict=True):
        text.set_color(color)

    fig.savefig('text-colored.typ')
    fig.savefig('text-colored.pdf')
    fig.savefig('text-colored.png')
    fig.savefig('text-colored.svg')
