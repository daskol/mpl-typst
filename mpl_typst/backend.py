import pathlib
import subprocess
from datetime import date, datetime
from io import StringIO
from shutil import copyfileobj
from tempfile import TemporaryDirectory
from typing import Literal, Optional, Self, TextIO, Type

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

from mpl_typst.typst import Array, Block, Call, Content, Dictionary, Scalar
from mpl_typst.typst import Writer as TypstWriter

__all__ = ('FigureCanvas', 'FigureManager', 'TypstFigureCanvas',
           'TypstFigureManager', 'TypstGraphicsContext', 'TypstRenderer')

PROLOGUE = pathlib.Path(__file__).parent / 'prologue.typ'


class TypstRenderer(RendererBase):
    """Typst renderer handles drawing/rendering operations."""

    def __init__(self, figure: Figure, fout: TextIO,
                 metadata: dict[str, str] = {}):
        super().__init__()
        self.figure = figure
        self.fout = fout
        self.metadata = metadata

        self.width = self.figure.get_figwidth()
        self.height = self.figure.get_figheight()
        self.dpi = self.figure.dpi
        self.timestamp = datetime.now().replace(microsecond=0)

        self.writer: Optional[TypstWriter] = None
        self.main: Optional[Block] = None

    def __enter__(self) -> Self:
        # First of all, add some helpers for rendering at the beginning.
        with open(PROLOGUE) as fin:
            template = fin.read()
            text = template.replace('{{ date }}', self.timestamp.isoformat())
        self.fout.write(text)
        self.fout.write('\n')

        # Now configure document geometry and set metadata.
        title = 'none'
        if value := self.metadata.get('title'):
            escaped = value.replace('"', '\"')
            title = f'"{escaped}"'
        date_ = 'auto'
        if ts := self.metadata.get('date', self.timestamp.date()):
            if isinstance(ts, datetime):
                ts: date = ts.date()
            elif isinstance(ts, date):
                ts: date = ts
            elif isinstance(ts, str):
                ts: date = datetime.fromisoformat(ts).date()
            else:
                raise ValueError(f'Wrong format of date in metadata: {ts}.')
            date_ = (f'datetime(year: {ts.year}, month: {ts.month}, '
                     f'day: {ts.day})')
        self.fout.write(f'#set document(title: {title}, date: {date_})\n')
        self.fout.write(f'#set page(width: {self.width}in, '
                        f'height: {self.height}in, margin: 0pt)\n')
        self.fout.write('\n')

        # Create a main block for drawing.
        self.main = Block()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.fout.write('#')  # Escape command.
        self.writer = TypstWriter(self.fout)
        expr = Call('block', self.main, spacing=Scalar(0, 'pt'),
                    above=Scalar(0, 'pt'), below=Scalar(0, 'pt'),
                    width=Scalar(100, '%'), height=Scalar(100, '%'))
        expr.to_string(self.writer)

    def draw_image(self, gc: GraphicsContextBase, x: float, y: float,
                   im: ArrayLike, transform: Affine2DBase | None = None):
        raise NotImplementedError

    def draw_path(self, gc: GraphicsContextBase, path: Path,
                  transform: Transform, rgbFace: ColorType | None = None):
        # Transform y-coordinates since Oy axis is flipped.
        def normalize(coords) -> tuple[float, ...]:
            result = []
            for ix, coord in enumerate(coords):
                if (ix % 2) == 1:
                    coord = self.height - coord / self.dpi
                else:
                    coord = coord / self.dpi
                result.append(coord)
            return tuple(result)

        # Configure basic appearance of a line.
        if (capstyle := gc.get_capstyle()) == 'projecting':
            capstyle = 'square'
        colour = Call('rgb', *[Scalar(c * 100, '%') for c in gc.get_rgb()])
        stroke = Call(
            'stroke',
            paint=colour,
            thickness=Scalar(gc.get_linewidth(), 'pt'),
            cap=Scalar(capstyle),
            join=Scalar(gc.get_joinstyle()),
        )

        # Configure appearance of dashed line.
        (offset, bounds) = gc.get_dashes()
        if bounds:
            bounds = Array([Scalar(bound, 'pt') for bound in bounds])
            if offset == 0:
                stroke.kwargs.update({
                    'dash': Dictionary({
                        'array': bounds,
                        'phase': Scalar(offset, 'pt'),
                    })
                })
            else:
                stroke.kwargs.update({'dash': bounds})

        # Construct a `path` routine invokation.
        line = Call('path', stroke=stroke)
        for points, code in path.iter_segments(transform):
            points = normalize(points)
            match code:
                case Path.STOP:
                    pass
                case Path.MOVETO | Path.LINETO:
                    x, y = points
                    line.args.append(Array([Scalar(x, 'in'), Scalar(y, 'in')]))
                case Path.CURVE3:
                    cx, cy, px, py = points
                    p = Array([Scalar(px, 'in'), Scalar(py, 'in')])
                    c = Array([Scalar(cx - px, 'in'), Scalar(cy - py, 'in')])
                    line.args.append(Array([p, ]))
                case Path.CURVE4:
                    inx, iny, outx, outy, px, py = points
                    p = Array([Scalar(px, 'in'), Scalar(py, 'in')])
                    inp = Array([Scalar(inx - px, 'in'),
                                 Scalar(iny - py, 'in')])
                    out = Array([Scalar(outx - px, 'in'),
                                 Scalar(outy - py, 'in')])
                    line.args.append(Array([p, inp, out]))
                case Path.CLOSEPOLY:
                    line.kwargs.update({'closed': True})

        # Place a line path relative to parent block element without layouting.
        place = Call('place', line, dx=Scalar(0, 'in'), dy=Scalar(0, 'in'))
        self.main.append(place)

    def draw_text(self, gc: GraphicsContextBase, x: float, y: float, s: str,
                  prop: FontProperties, angle: float,
                  ismath: bool | Literal['TeX'] = False, *,
                  mtext: Text | None = None):
        alignment = 'center + horizon'
        baseline = False
        fontsize = prop.get_size_in_points()
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
            alignment = f'{halign} + {valign}'
            fontsize = mtext.get_fontsize()
            angle = mtext.get_rotation()
        else:
            x = x / self.figure.dpi
            y = self.height + y / self.figure.dpi

        elem = Call('draw-text',
                    Content(s),
                    dx=Scalar(x, 'in'),
                    dy=Scalar(y, 'in'),
                    size=Scalar(fontsize, 'pt'),
                    alignment=alignment,
                    baseline=baseline,
                    angle=Scalar(360 - angle, 'deg'))
        self.main.append(elem)

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
        with open(filename, 'w') as fout:
            with TypstRenderer(self.figure, fout) as renderer:
                self.figure.draw(renderer)


# Now, just provide the standard names that `backend.__init__` is expecting.
FigureCanvas = TypstFigureCanvas
FigureManager = TypstFigureManager
