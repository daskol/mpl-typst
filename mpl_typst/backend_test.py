import pathlib
from io import BytesIO

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.figure import Figure
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.path import Path
from numpy.testing import assert_array_equal
from PIL import Image

from mpl_typst import rc_context
from mpl_typst.testing import assert_anchored_places

data_dir = pathlib.Path(__file__).parent / 'testdata'


def to_array(fig, dpi: int = 144, **kwargs) -> np.ndarray:
    buf = BytesIO()
    fig.savefig(buf, dpi=dpi, format='png', **kwargs)
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf)
    return np.asarray(img)


def clipped_line_figure():
    fig, ax = plt.subplots(figsize=(2, 2), dpi=100)
    fig.subplots_adjust(left=0.25, right=0.75, bottom=0.25, top=0.75)
    ax.plot([0, 1], [0, 1], linewidth=40)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    return fig, ax


def rect_figure(hatch=None) -> Figure:
    rect = Rectangle(
        (0.15, 0.15), 0.7, 0.7,
        facecolor='white', edgecolor='black', hatch=hatch, linewidth=1.0)

    fig, ax = plt.subplots(figsize=(2, 2), dpi=100)
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax.set_axis_off()
    ax.set_aspect('equal')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.add_patch(rect)
    return fig


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

    def test_draw_path_clips_to_bbox(self):
        fig, ax = clipped_line_figure()
        fig.canvas.draw()
        bbox = ax.bbox.frozen()

        with rc_context():
            actual = to_array(fig, dpi=100)

        # This is heuristics that allows to distinguish blue line and mitigate
        # antialiasing issues.
        height, width, _ = actual.shape
        rgb = actual[..., :3].astype(np.int16)
        red, green, blue = np.moveaxis(rgb, -1, 0)
        blue_line = (blue > red + 20) & (blue > green + 20) & (blue > 80)

        x0 = max(0, int(np.floor(bbox.x0)))
        x1 = min(width, int(np.ceil(bbox.x1)))
        y0 = max(0, int(np.floor(height - bbox.y1)))
        y1 = min(height, int(np.ceil(height - bbox.y0)))

        outside = np.ones(blue_line.shape, dtype=bool)
        outside[y0:y1, x0:x1] = False

        assert not blue_line[outside].any()

    def test_draw_path_bbox_pixels(self):
        fig, _ = clipped_line_figure()

        with rc_context():
            actual = to_array(fig, dpi=100)

        expected = Image.open(data_dir / 'draw_path_bbox.png')
        assert_array_equal(actual, expected)

    def test_draw_path_hatched_rect_markup(self):
        buf = BytesIO()

        with rc_context():
            fig = rect_figure(hatch='///')
            fig.savefig(buf, format='typ')

        text = buf.getvalue().decode()
        assert 'rect(' in text
        assert 'clip: true' in text
        assert 'curve.move' in text
        assert 'curve.line' in text
        assert 'thickness: 1.0pt' in text
        assert_anchored_places(text)

    def test_draw_path_clipped_box_markup(self):
        buf = BytesIO()

        with rc_context():
            fig, _ = clipped_line_figure()
            fig.savefig(buf, format='typ')

        text = buf.getvalue().decode()
        assert_anchored_places(text)

    @pytest.mark.parametrize('hatch', ['///', 'x/', '.'])
    def test_draw_path_hatched_rect_pixels(self, hatch: str):
        with rc_context():
            actual_fig = rect_figure(hatch=hatch)
            actual = to_array(actual_fig, dpi=100)
            plain_fig = rect_figure()
            plain = to_array(plain_fig, dpi=100)

        rgb = actual[..., :3].astype(np.int16)
        black = (rgb < 120).all(axis=-1)

        plain_rgb = plain[..., :3].astype(np.int16)
        plain_black = (plain_rgb < 120).all(axis=-1)

        # Interior of hatched image must be darker (more black).
        interior = np.s_[35:165, 35:165]
        assert black[interior].sum() > plain_black[interior].sum() + 200

    def test_draw_path_hatched_rect_pixels_golden(self):
        with rc_context():
            actual_fig = rect_figure(hatch='///')
            actual = to_array(actual_fig, dpi=100)

        expected = Image.open(data_dir / 'hatched_rect.png')
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
    def test_print_typ(self, how: str, tmp_path: pathlib.Path):
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
            fname: str | pathlib.Path = filename
            if how == 'str':
                fname = str(fname)
            with rc_context():
                fig.savefig(fname, format='typ')
            assert filename.stat().st_size > 0
        else:
            raise RuntimeError(f'Unexpected test parameter: how={how}.')
