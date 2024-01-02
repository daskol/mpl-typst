"""Package `mpl_typst` provides a :py:`matplotlib` backend for rendering
directly to Typst as well as rendering to PDF, PNG, SVG indirectly through
Typst renderer.

One can import `mpl_typst.as_default` module in order to use `mpl_typst`
backend by default.

.. code:: python

   import mpl_typst.as_default

Or one can configure it manually.

.. code:: python

   import matplotlib
   import mpl_typst
   mpl.use('module://mpl_typst')

Also, it is possible to use rendering context as usual to override backend.

.. code:: python

   import matplotlib as mpl
   import mpl_typst
   with mpl.rc_context({'backend': 'module://mpl_typst'}):
       ...
"""

from contextlib import contextmanager
from typing import Any

import matplotlib as mpl

from mpl_typst.backend import (FigureCanvas, FigureManager, TypstFigureCanvas,
                               TypstFigureManager, TypstRenderer)

__all__ = ('BACKEND', 'FigureCanvas', 'FigureManager', 'TypstFigureCanvas',
           'TypstFigureManager', 'TypstGraphicsContext', 'TypstRenderer',
           'rc_context', 'use')

# Backend specification for use with `matplotlib.use`
BACKEND = 'module://mpl_typst'


@contextmanager
def rc_context(rc: dict[str, Any] | None = None, fname=None):
    """A shortcut for using Typst as default backend in a context.

    It forward all arguments to original :py:`matplotlib.rc_context` context
    manager but it enforces use of `mpl_typst` backend in the beginning of
    newly created context.

    .. code:: python

       import mpl_typst
       with mpl_typst.rc_context():
           ...
    """
    original_backend = mpl.rcParams.get('backend')
    with mpl.rc_context(rc, fname):
        mpl.use(BACKEND)
        yield
        mpl.use(original_backend)


def use(*, force: bool = True):
    """Set Typst rendering backend as default on (see :py:`matplotlib.use`)."""
    mpl.use(BACKEND)
