from matplotlib.font_manager import FontProperties

from mpl_typst.backend import TypstGraphicsContext


def test_measure_text():
    font = FontProperties(family='sans-serif', style='normal',
                          variant='normal', weight='normal',
                          stretch='normal', size=10.0)
    print(font.get_fontconfig_pattern())
    gc = TypstGraphicsContext()
    shape = gc.measure_text('lp', font)
    print(shape)
