import math

import matplotlib as mpl
import numpy as np

__all__ = ('LogFormatter', 'LogFormatterSciNotation')


def _is_close_to_int(x):
    return math.isclose(x, round(x))


class LogFormatterTypst(mpl.ticker.LogFormatter):
    """Format values for log axis using ``exponent = log_base(value)``.
    """

    def _non_decade_format(self, sign_string, base, fx, usetex):
        """Return string for non-decade locations."""
        return r'$\mathdefault{%s%s^{%.2f}}$' % (sign_string, base, fx)

    def __call__(self, x, pos=None):
        # docstring inherited
        if x == 0:  # Symlog
            return r'$0$'

        sign_string = '-' if x < 0 else ''
        x = abs(x)
        b = self._base

        # only label the decades
        fx = math.log(x) / math.log(b)
        is_x_decade = _is_close_to_int(fx)
        exponent = round(fx) if is_x_decade else np.floor(fx)
        coeff = round(b ** (fx - exponent))

        if self.labelOnlyBase and not is_x_decade:
            return ''
        if self._sublabels is not None and coeff not in self._sublabels:
            return ''

        if is_x_decade:
            fx = round(fx)

        # use string formatting of the base if it is not an integer
        if b % 1 == 0.0:
            base = fr'{b:.0f}'
        else:
            base = fr'{b:s}'

        if abs(fx) < mpl.rcParams['axes.formatter.min_exponent']:
            return fr'${sign_string:s}{x:g}$'
        elif not is_x_decade:
            usetex = mpl.rcParams['text.usetex']
            return self._non_decade_format(sign_string, base, fx, usetex)
        else:
            return fr'${sign_string:s}{base:s}^{fx:d}$'


class LogFormatterSciNotation(LogFormatterTypst):
    """
    Format values following scientific notation in a logarithmic axis.
    """

    def _non_decade_format(self, sign_string, base, fx, usetex):
        """Return string for non-decade locations."""
        b = float(base)
        exponent = math.floor(fx)
        coeff = b ** (fx - exponent)
        if _is_close_to_int(coeff):
            coeff = round(coeff)
        return fr'${sign_string:s}{coeff:g} times {base:s}^{exponent}$'
