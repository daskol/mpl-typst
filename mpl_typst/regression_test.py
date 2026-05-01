from io import BytesIO

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from numpy.testing import assert_array_equal
from PIL import Image

from mpl_typst import rc_context
from mpl_typst.testing import (
    data_dir, to_array, typ_block_size, typ_text_position)


class TestIssue27:

    @staticmethod
    def figure(layout: str | None = None) -> Figure:
        fig = plt.figure(figsize=(3, 1.5), dpi=100, layout=layout)
        x = np.array([[1], [1]])
        plt.imshow(x, aspect='auto', cmap='viridis')
        plt.colorbar(label='Embedding Value')
        plt.xlabel('Embedding Dimension')
        plt.ylabel('Timestep')
        return fig

    def test_against_reference(self):
        with rc_context():
            fig = TestIssue27.figure()
            actual = to_array(fig, dpi=100)

        expected = Image.open(data_dir / 'regression/issue27.png')
        assert_array_equal(actual, expected)

    def test_loose_content_contains_xlabel(self):
        loose = BytesIO()
        with rc_context():
            fig = TestIssue27.figure()
            fig.savefig(loose, format='typ', pad_inches=0)

        text = loose.getvalue().decode()
        _, loose_height = typ_block_size(text)
        _, xlabel_y = typ_text_position(text, 'Embedding Dimension')

        assert loose_height > 1.5
        assert xlabel_y < loose_height

    def test_constrained_layout_keeps_figure_geometry(self):
        fixed = BytesIO()
        with rc_context():
            fig = TestIssue27.figure(layout='constrained')
            fig.savefig(fixed, format='typ', pad_inches=0)

        text = fixed.getvalue().decode()
        _, fixed_height = typ_block_size(text)
        _, xlabel_y = typ_text_position(text, 'Embedding Dimension')

        assert fixed_height == 1.5
        assert xlabel_y < fixed_height

    def test_tight_bbox_expands_geometry(self):
        tight = BytesIO()
        with rc_context():
            fig = TestIssue27.figure()
            fig.savefig(tight, format='typ', bbox_inches='tight', pad_inches=0)

        _, tight_height = typ_block_size(tight.getvalue().decode())
        assert tight_height > 1.5
