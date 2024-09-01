import pathlib
from io import BytesIO

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from numpy.testing import assert_array_equal
from PIL import Image

from mpl_typst import rc_context

data_dir = pathlib.Path(__file__).parent / 'testdata'


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

            buf = BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
            buf.seek(0)

            img = Image.open(buf)
            return np.asarray(img)

        # Use `mpl_typst` renderer.
        with rc_context():
            actual = render_figure()

        # Load ground-truth image.
        img = Image.open(data_dir / 'draw_path.png')
        expected = np.asarray(img)
        assert_array_equal(actual, expected)
