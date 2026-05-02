import pathlib
import re
from io import BytesIO

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

data_dir = pathlib.Path(__file__).parent / 'testdata'

RE_BLOCK_SIZE = re.compile(
    r'width: (?P<width>[0-9.]+)in,\n\s+height: (?P<height>[0-9.]+)in\)')
RE_DRAW_TEXT = re.compile(
    r'\[(?P<text>[^\]]+)\],\n'
    r'\s+dx: (?P<dx>-?[0-9.]+)in,\n'
    r'\s+dy: (?P<dy>-?[0-9.]+)in,')


def to_array(fig: Image, dpi: int = 144, **kwargs) -> np.ndarray:
    buf = BytesIO()
    try:
        fig.savefig(buf, dpi=dpi, format='png', **kwargs)
        buf.seek(0)
        img = Image.open(buf)
        return np.asarray(img)
    finally:
        plt.close(fig)


def typ_block_size(text: str) -> tuple[float, float]:
    match = None
    for match in RE_BLOCK_SIZE.finditer(text):
        pass
    if match is None:
        raise AssertionError('No Typst block size found.')
    return float(match['width']), float(match['height'])


def typ_text_position(source: str, text: str) -> tuple[float, float]:
    for match in RE_DRAW_TEXT.finditer(source):
        if match['text'] == text:
            return float(match['dx']), float(match['dy'])
    raise AssertionError(f'Typst text not found: {text!r}.')
