#!/usr/bin/env python

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.axes_grid1.axes_divider import make_axes_locatable

from mpl_typst import rc_context

mpl.rcParams.update({
    'font.family': 'serif',
    'font.size': 8,
    'axes.labelsize': 8,
    'legend.fontsize': 6,
    'xtick.labelsize': 6,
    'ytick.labelsize': 6,
    'axes.titlesize': 8,
})

xticks = [512, 2048, 4096, 8192, 16384, 65536]
yticks = [8, 32, 64, 96, 128]
values = np.array([
    0.6, 0.0, 0.1, 0.1, -0.2, 0.7, -0.0, -0.0, 0.2, 0.1, -0.1, 1.7, 0.0, 0.1,
    0.1, 0.2, 0.1, 1.8, 0.0, 0.1, -0.0, 0.2, 0.5, 0.9, 0.0, 0.1, 0.2, 0.3, 0.8,
    2.1
]).reshape(5, 6)

with rc_context({
        'text.parse_math': False,
        'text.usetex': False,
        'axes.formatter.use_mathtext': False,
}):
    fig, ax = plt.subplots(figsize=(3.25, 2.01), layout='constrained')
    ax.set_aspect('equal')

    width, height = values.T.shape
    xs, ys = np.mgrid[:width + 1, :height + 1]
    img = ax.pcolor(xs, ys, values.T)

    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='5%', pad=0.1)
    fig.colorbar(img, cax)

    ax.set_xlabel('Number of tokens')
    ax.set_xticks(np.arange(len(xticks)))
    ax.set_xticklabels([f'{x:.1f}' if x < 1 else int(x) for x in xticks])

    ax.set_ylabel('Rank $r$')
    ax.set_yticks(np.arange(len(yticks)))
    ax.set_yticklabels([str(x) for x in yticks])
    ax.invert_yaxis()

    fig.savefig('pcolor.pdf')
    fig.savefig('pcolor.png')
    fig.savefig('pcolor.svg')
    fig.savefig('pcolor.typ')
