# Gallery

## Overview

This directory contains small examples that show how `mpl-typst` exports
Matplotlib figures as Typst markup and how those generated `.typ` files can be
included in a larger Typst document.

![Example document.][main]

| File                                           | Purpose                                                 |
| ---------------------------------------------- | ------------------------------------------------------- |
| [`main.typ`](./main.typ)                       | A two-column Typst document with Matplotlib figures.    |
| [`hist-hatched.py`](./hist-hatched.py)         | A histogram with colored bars and hatch patterns.       |
| [`line-plot-simple.py`](./line-plot-simple.py) | A compact line plot with labels, legend, and math text. |
| [`pcolor.py`](./pcolor.py)                     | A pseudocolor plot with a separate colorbar axis.       |
| [`spy.py`](./spy.py)                           | A sparse matrix-style plot generated with `Axes.spy`.   |

The composed gallery page currently uses `line-plot-simple.typ` and
`hist-hatched.typ`. The other scripts are standalone examples that can be run
manually.

[main]: ./main.png
