from inspect import getfile
from io import BytesIO
from pathlib import Path
from typing import Any, ClassVar, Mapping

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from numpy.testing import assert_array_equal
from PIL import Image

DATA_DIR = Path(__file__).parent / 'testdata'


def render_reference(fig: Figure, *, dpi: int,
                     savefig_kwargs: Mapping[str, Any]) -> np.ndarray:
    """Render a rasterized figure to PNG and return pixel array."""
    from . import rc_context

    try:
        buf = BytesIO()
        with rc_context():
            fig.savefig(buf, dpi=dpi, format='png', **savefig_kwargs)
        buf.seek(0)
        return np.asarray(Image.open(buf))
    finally:
        plt.close(fig)


class IssueRegression:
    """A common type base for regresions reported by users."""

    reference_dpi: ClassVar[int] = 144

    reference_savefig_kwargs: ClassVar[Mapping[str, Any]] = {}

    @staticmethod
    def figure() -> Figure:
        raise NotImplementedError

    @classmethod
    def reference_path(cls) -> Path:
        issue = cls.__name__.removeprefix('Test').lower()
        data_dir = Path(getfile(cls)).parent / 'testdata'
        return data_dir / f'{issue}.png'

    def test_reference(self):
        cls = type(self)
        reference = cls.reference_path()
        assert reference.exists(), f'Missing reference image: {reference}.'

        actual = render_reference(cls.figure(), dpi=cls.reference_dpi,
                                  savefig_kwargs=cls.reference_savefig_kwargs)
        expected = np.asarray(Image.open(reference))
        assert_array_equal(actual, expected)
