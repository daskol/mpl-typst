import pathlib
import subprocess
from io import StringIO
from shutil import copyfileobj
from tempfile import TemporaryDirectory
from typing import IO, Literal, Type

from matplotlib.backend_bases import (FigureCanvasBase, FigureManagerBase,
                                      GraphicsContextBase, RendererBase)
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.path import Path
from matplotlib.text import Text
from matplotlib.transforms import (Affine2DBase, Bbox, BboxBase, Transform,
                                   TransformedPath)
from matplotlib.typing import ColorType
from numpy.typing import ArrayLike

__all__ = ('FigureCanvas', 'FigureManager', 'TypstFigureCanvas',
           'TypstFigureManager', 'TypstGraphicsContext', 'TypstRenderer')


class TypstRenderer(RendererBase):
    """Typst renderer handles drawing/rendering operations."""

    def __init__(self, figure: Figure, fout: IO, width: float, height: float,
                 dpi: float):
        super().__init__()
        self.figure = figure
        self.fout = fout
        self.width = width
        self.height = height
        self.dpi = dpi

    def draw_image(self, gc: GraphicsContextBase, x: float, y: float,
                   im: ArrayLike, transform: Affine2DBase | None = None):
        pass

    def draw_path(self, gc: GraphicsContextBase, path: Path,
                  transform: Transform, rgbFace: ColorType | None = None):
        buf = StringIO()

        def add_point(point):
            x, y = point
            buf.write(f'({x}in, {y}in)')

        def normalize(coords) -> tuple[float, ...]:
            result = []
            for ix, coord in enumerate(coords):
                if (ix % 2) == 1:
                    coord = self.height - coord / self.dpi
                else:
                    coord = coord / self.dpi
                result.append(coord)
            return tuple(result)

        closed = False
        gc.get_linewidth()

        stroke = StringIO()
        stroke.write('stroke(')
        # print(gc.get_rgb())
        components = ', '.join(f'{c * 100:f}%' for c in gc.get_rgb())
        paint = f'rgb({components})'
        stroke.write(f'paint: {paint}, ')
        stroke.write(f'thickness: {gc.get_linewidth()}pt, ')
        if (capstyle := gc.get_capstyle()) == 'projecting':
            capstyle = 'square'
        stroke.write(f'cap: "{capstyle}", ')
        stroke.write(f'join: "{gc.get_joinstyle()}", ')
        (offset, bounds) = gc.get_dashes()
        if bounds:
            bounds = ', '.join(f'{x}pt' for x in bounds)
            if offset == 0:
                dash = f'(array: ({bounds}), phase: {offset}pt)'
            else:
                dash = f'({bounds})'
            stroke.write(f'dash: {dash}, ')
        stroke.write(')')
        stroke = stroke.getvalue()
        for points, code in path.iter_segments(transform):
            points = normalize(points)
            match code:
                case Path.STOP:
                    pass
                case Path.MOVETO | Path.LINETO:
                    x, y = points
                    buf.write(f'  ')
                    add_point(points)
                    buf.write(',\n')
                case Path.CURVE3:
                    cx, cy, px, py = points
                    buf.write('  (')
                    add_point((px, py))
                    buf.write(', ')
                    add_point((cx - px, cy - py))
                    buf.write('),\n')
                case Path.CURVE4:
                    inx, iny, outx, outy, px, py = points
                    buf.write('  (')
                    add_point((px, py))
                    buf.write(', ')
                    add_point((inx - inx, outy - outy))
                    buf.write('),\n')
                case Path.CLOSEPOLY:
                    closed = True
                    point = points
        self.fout.write(f'place(dx: 0in, dy: 0in,\n    path(')
        self.fout.write(f'stroke: {stroke}, ')
        if closed:
            self.fout.write('closed: true,')
        self.fout.write('\n')
        self.fout.write(buf.getvalue())
        self.fout.write('))\n')

    def draw_text(self, gc: GraphicsContextBase, x: float, y: float, s: str,
                  prop: FontProperties, angle: float,
                  ismath: bool | Literal['TeX'] = False, *,
                  mtext: Text | None = None):
        print((x, y), s, mtext, ismath, mtext.get_rotation(),
              mtext.get_rotation_mode())
        alignment = 'center + horizon'
        baseline = False
        fontsize = prop.get_size_in_points()
        # if mtext and (mtext.get_verticalalignment() != 'center_baseline'):
        if mtext:
            pos = mtext.get_unitless_position()
            x, y = mtext.get_transform().transform(pos)
            x = x / self.figure.dpi
            y = self.height - y / self.figure.dpi
            halign = mtext.get_horizontalalignment()
            valign = mtext.get_verticalalignment()
            match valign:
                case 'center':
                    valign = 'horizon'
                case 'center_baseline':
                    valign = 'horizon'
                    baseline = True
                case 'baseline':
                    valign = 'bottom'
                    baseline = True
            print(halign, '+', valign, baseline)
            alignment = f'{halign} + {valign}'
            fontsize = mtext.get_fontsize()
            angle = mtext.get_rotation()
        else:
            x = x / self.figure.dpi
            y = self.height + y / self.figure.dpi
        # self.fout.write(f'  place(dx: {x}in, dy: {y}in,\n    text([{s}]))\n')
        self.fout.write(f'  draw_text(dx: {x}in, dy: {y}in, ')
        self.fout.write(f'size: {fontsize}pt, ')
        self.fout.write(f'alignment: {alignment}, ')
        if baseline:
            self.fout.write(f'baseline: true, ')
        self.fout.write(f'angle: {360 - angle}deg, ')
        self.fout.write(f'text([{s}]))\n')

    def flipy(self):
        """Axis Oy points to bottom."""
        return True

    def get_canvas_width_height(self) -> tuple[float, float]:
        return self.width, self.height

    def get_text_width_height_descent(
            self, s: str, prop: FontProperties,
            ismath: bool | Literal['TeX'] = False,
        ) -> tuple[float, float, float]:
        return super().get_text_width_height_descent(s, prop, ismath)

    def new_gc(self) -> Type[GraphicsContextBase]:
        return TypstGraphicsContext()

    def points_to_pixels(self, points):
        return points  # if backend doesn't have dpi, e.g., postscript or svg


class TypstGraphicsContext(GraphicsContextBase):
    """In Typst, all the work is done by the renderer, mapping line styles to
    Typst calls.
    """


class TypstFigureManager(FigureManagerBase):
    """Non-interactive backend requires nothing."""


class TypstFigureCanvas(FigureCanvasBase):
    """The canvas the figure renders into.  Calls the draw and print fig
    methods, creates the renderers, etc.

    Attributes
    ----------
    figure : `~matplotlib.figure.Figure`
        A high-level Figure instance
    """

    filetypes = {**FigureCanvasBase.filetypes, 'typ': 'Typst Markup'}

    fixed_dpi: float = 144

    manager_class = TypstFigureManager

    def draw(self):
        """Draw the figure using the renderer."""
        self.figure.draw_without_rendering()
        super().draw()

    def get_default_filetype(self):
        return 'typ'

    def print_pdf(self, filename, **kwargs):
        raise NotImplementedError

    def print_png(self, filename, **kwargs):
        with TemporaryDirectory() as tmpdir:
            inp_path = pathlib.Path(tmpdir) / 'main.typ'
            out_path = inp_path.with_suffix('.png')
            self.print_typ(inp_path, **kwargs)
            cmd = ['typst', 'compile', f'--root={tmpdir}', '--format=png',
                   str(inp_path), str(out_path)]
            print(f'execute command: "{" ".join(cmd)}"')
            proc = subprocess.run(cmd, capture_output=True)
            with open(out_path, 'rb') as fin, open(filename, 'wb') as fout:
                copyfileobj(fin, fout)

    def print_svg(self, filename, **kwargs):
        raise NotImplementedError

    def print_typ(self, filename, **kwargs):
        width = self.figure.get_figwidth()
        height = self.figure.get_figheight()
        dpi = self.figure.dpi
        with open(filename, 'w') as fout:
            fout.write('#set document(title: "testing")\n')
            fout.write(
                f'#set page(width: {width}in, height: {height}in, margin: 0pt)\n'
            )
            fout.write(PREABMBLE)
            fout.write(
                f'#block(spacing: 0pt, above: 0pt, below: 0pt, width: 100%, height: 100%, {{\n'
            )
            renderer = TypstRenderer(self.figure, fout, width, height, dpi)
            self.figure.draw(renderer)
            fout.write('})\n')


# Now, just provide the standard names that `backend.__init__` is expecting.
FigureCanvas = TypstFigureCanvas
FigureManager = TypstFigureManager

PREABMBLE = """
#let draw_text(dx: 0pt, dy: 0pt, size: 10pt, alignment: center + horizon, baseline: false, angle: 0deg, body) = style(styles => {
  let top-edge = "cap-height"
  let bot-edge = "bounds"
  let valign = alignment.y;
  if baseline and valign == bottom {
    bot-edge = "baseline"
  }

  if baseline and valign == horizon {
    bot-edge = "baseline"
  }

  let content = text(size: size, top-edge: top-edge, bottom-edge: bot-edge, body)
  let shape = measure(content, styles)

  let px = dx
  if alignment.x == left {
    // Do nothing.
  } else if alignment.x == center {
    px -= shape.width / 2
  } else if alignment.x == right {
    px -= shape.width
  }

  let py = dy
  if valign == top {
    // Do nothing.
  } else if valign == horizon {
    py -= shape.height / 2
  } else if valign == bottom {
    py -= shape.height
  }

  if angle != 0deg {
    content = rotate(angle, origin: alignment, content)
  }
  place(dx: px, dy: py, content)
})
"""
