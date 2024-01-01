#!/usr/bin/env python3

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backend_bases import register_backend

import backend_typst

mpl.use('module://backend_typst')
register_backend('typ', 'backend_typst', 'Typst markup')
print('current backend is', mpl.get_backend())

fig, ax = plt.subplots()
ax.plot([i ** 2 for i in range(10)], label='x^2')
ax.legend()
fig.savefig('out.typ')
