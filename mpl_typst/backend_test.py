import pathlib
from io import BytesIO

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from numpy.testing import assert_array_equal
from PIL import Image

from mpl_typst import rc_context

data_dir = pathlib.Path(__file__).parent / 'testdata'


def to_array(fig: Image, dpi: int = 144, **kwargs) -> np.ndarray:
    buf = BytesIO()
    fig.savefig(buf, dpi=dpi, format='png', **kwargs)
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf)
    return np.asarray(img)


class TestTypstRenderer:

    def test_draw_path(self):
        verts = [
            (Path.MOVETO, (0.0, 0.0)),
            (Path.LINETO, (0.0, 1.0)),
            (Path.LINETO, (1.0, 1.0)),
            (Path.LINETO, (1.0, 0.0)),
            (Path.CLOSEPOLY, (0.0, 0.0)),
            (Path.MOVETO, (-1, 2)),
            (Path.LINETO, (0, 2)),
            (Path.CURVE3, (1, 1)),
            (Path.CURVE3, (2, 2)),
            (Path.CURVE3, (3, 3)),
            (Path.CURVE3, (2, 4)),
            (Path.CURVE4, (-1, 4)),
            (Path.CURVE4, (1, 6)),
            (Path.CURVE4, (1, 3)),
            (Path.LINETO, (1, 2)),
            (Path.MOVETO, (2, -1)),
            (Path.LINETO, (2.0, 0.0)),
            (Path.CURVE4, (2.2, 1.0)),
            (Path.CURVE4, (3.0, 0.8)),
            (Path.CURVE4, (2.8, 0.0)),
            (Path.CLOSEPOLY, (0, 0)),
            (Path.MOVETO, (4, 1)),
            (Path.CURVE4, (4.2, 1.0)),
            (Path.CURVE4, (5.0, 0.8)),
            (Path.CURVE4, (4.8, 0.0)),
            (Path.CURVE4, (4, -1)),
            (Path.CURVE4, (5.0, -1)),
            (Path.CURVE4, (5, 0)),
            (Path.CURVE3, (6, 2)),
            (Path.CURVE3, (5, 2)),
            (Path.LINETO, (3, 3)),
            (Path.MOVETO, (4, 3)),
            (Path.CURVE3, (5, 3)),
            (Path.CURVE3, (5, 4)),
            (Path.CLOSEPOLY, (0, 0)),
            (Path.LINETO, (5, 5)),
            (Path.CLOSEPOLY, (0, 0)),
        ]

        codes, coords = zip(*verts)
        path = Path(coords, codes)
        patch = PathPatch(path, facecolor='orange', lw=2)

        def render_figure() -> BytesIO:
            fig, ax = plt.subplots()
            ax.axis('off')
            ax.add_patch(patch)
            ax.set_xlim(-2, 6)
            ax.set_ylim(-2, 6)
            return to_array(fig, dpi=100, bbox_inches='tight', pad_inches=0)

        # Use `mpl_typst` renderer.
        with rc_context():
            actual = render_figure()

        # Load ground-truth image.
        img = Image.open(data_dir / 'draw_path.png')
        expected = np.asarray(img)
        assert_array_equal(actual, expected)

    @pytest.mark.parametrize('dpi', [72, 100, 144])
    def test_draw_image_lenna(self, dpi: int):
        img = Image.open(data_dir / 'lenna.png')

        def render():
            fig, ax = plt.subplots(figsize=(512 / 72,) * 2, dpi=72)
            plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
            ax.axis('off')
            ax.imshow(img)
            return to_array(fig, dpi)

        with rc_context():
            actual = render()
        desired = render()

        # Compare Lenna rerendered with `matplotlib` and `mpl-typst`.
        assert_array_equal(actual, desired)

    @pytest.mark.parametrize('dpi', [72, 100, 144])
    def test_draw_image_spy(self, dpi: int):
        rng = np.random.default_rng(42)
        xs = rng.integers(0, 2, size=(8, 16))

        def render():
            fig, ax = plt.subplots(figsize=(3, 2))
            ax.spy(xs)
            ax.set_xticks([])
            ax.set_yticks([])
            return to_array(fig, dpi)

        with rc_context():
            actual = render()
        desired = render()

        # Compare with `matplotlib` rendering.
        ix, *_ = np.nonzero(actual - desired)
        nnz = len(ix)
        total = np.prod(actual.shape)
        expected = {72: 2, 100: 4, 144: 1}[dpi]
        assert (ratio := 100 * nnz / total) < expected, \
            f'Number of mismatched pixels exceed {expected}%: {ratio:.2f}%.'

        # Compare with the previous renderings.
        reference = Image.open(data_dir / f'spy{dpi:03d}.png')
        assert_array_equal(actual, reference)


class TestTypstFigureCanvas:

    @pytest.mark.parametrize('how', ['buffer', 'path', 'str'])
    def test_print_typ(self, how: str, tmp_path: Path):
        fig, ax = plt.subplots(1, 1)
        x = np.linspace(0.0, 2 * np.pi, 100)
        y = np.sin(x)
        ax.plot(x, y)

        if how == 'buffer':
            buffer = BytesIO()
            with rc_context():
                fig.savefig(buffer, format='typ')
            assert buffer.tell() > 0
        elif how in ('path', 'str'):
            filename = tmp_path / 'output.typ'
            fname: str | Path = filename
            if how == 'str':
                fname = str(fname)
            with rc_context():
                fig.savefig(fname, format='typ')
            assert filename.stat().st_size > 0
        else:
            raise RuntimeError(f'Unexpected test parameter: how={how}.')
