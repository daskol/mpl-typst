import base64
import itertools
import pathlib
import re
import subprocess
from codecs import getwriter
from datetime import date, datetime
from io import BytesIO
from os import PathLike
from shutil import copyfileobj, move
from tempfile import TemporaryDirectory
from typing import IO, Any, Literal, Optional, Self, Type

import matplotlib as mpl
import numpy as np
from matplotlib import get_cachedir
from matplotlib.backend_bases import (
    FigureCanvasBase, FigureManagerBase, GraphicsContextBase, RendererBase,
    register_backend)
from matplotlib.backends.backend_mixed import MixedModeRenderer
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.path import Path
from matplotlib.text import Text
from matplotlib.transforms import Affine2DBase, Transform
from numpy.typing import ArrayLike
from PIL import Image, ImageOps

# Module `matplotlib.typing` has been introduced in matplotlib@3.8 but the
# latest Ubuntu LTS 24.04 provides matplotlib@3.6. Since we are not ready to
# abandont typing hints and support of the most popular distros is desirable,
# we keep this version check until Ubuntu LTS 26.04.
#
# https://github.com/daskol/mpl-typst/issues/24
if mpl.__version_info__ >= (3, 8):
    from matplotlib.typing import ColorType
else:
    ColorType = Any

from mpl_typst.config import Config, compiler
from mpl_typst.typst import (
    Array, Block, Call, Content, Dictionary, Scalar, Writer as TypstWriter)

__all__ = ('FigureCanvas', 'FigureManager', 'TypstFigureCanvas',
           'TypstFigureManager', 'TypstGraphicsContext', 'TypstRenderer',
           'TypstRenderingError')

PROLOGUE = pathlib.Path(__file__).parent / 'prologue.typ'

RE_ERROR = re.compile(
    r'^(?P<filename>.*):(?P<line>\d+):(?P<column>\d+): error: (?P<reason>.*)$')

TPL_ERROR = '  {filename}:{line}:{column}: {reason}'


class TypstRenderingError(RuntimeError):
    """Represent an error occured in rendering target with Typst binary."""

    def __init__(self, stdout: str, stderr: str, errors: list[dict[str, Any]]):
        header = (f'Typst renderer failed with {len(errors)} errors. '
                  'They are shown below')
        lines = [header]
        for error in errors:
            lines.append(TPL_ERROR.format(**error))
        message = '\n'.join(lines)

        super().__init__(message)
        self.stdout = stdout
        self.stderr = stderr
        self.errors = errors

    def to_dict(self):
        return {'stdout': self.stdout, 'stderr': self.stderr,
                'errors': self.errors}


class TypstRenderer(RendererBase):
    """Typst renderer handles drawing/rendering operations."""

    def __init__(self, figure: Figure, fout: IO[str],
                 config: Config | None = None, path: PathLike | None = None,
                 metadata: dict[str, str] = {}, image_dpi=72):
        super().__init__()
        self.config: Config = config or Config()
        self.figure = figure
        self.fout = fout
        self.image_dpi = image_dpi
        self.metadata = metadata

        if path is None:
            self.path = None
        else:
            self.path = pathlib.Path(path)

        self.width = self.figure.get_figwidth()
        self.height = self.figure.get_figheight()
        self.dpi = figure.dpi
        self.timestamp = datetime.now().replace(microsecond=0)

        self._image_counter = itertools.count()

        self.writer: Optional[TypstWriter] = None
        self.main: Optional[Block] = None

    def __enter__(self) -> Self:
        # First of all, add some helpers for rendering at the beginning.
        with open(PROLOGUE) as fin:
            template = fin.read()
            text = template.replace('{{ date }}', self.timestamp.isoformat())
            text = text.replace('{{ preamble }}', self.config.preamble)
        self.fout.write(text)
        self.fout.write('\n')

        # Now configure document geometry and set metadata.
        if self.metadata:
            title = 'none'
            if value := self.metadata.get('title'):
                escaped = value.replace('"', '"')
                title = f'"{escaped}"'

            author = '()'
            if value := self.metadata.get('author'):
                escaped = value.replace('"', '"')
                author = f'"{value}"'

            date_ = 'auto'
            if ts := self.metadata.get('date', self.timestamp.date()):
                if isinstance(ts, datetime):
                    ts: date = ts.date()
                elif isinstance(ts, date):
                    ts: date = ts
                elif isinstance(ts, str):
                    ts: date = datetime.fromisoformat(ts).date()
                else:
                    raise ValueError(f'Wrong date format in metadata: {ts}.')
                date_ = (f'datetime(year: {ts.year}, month: {ts.month}, '
                         f'day: {ts.day})')

            self.fout.write(f'#set document(title: {title}, author: {author}, '
                            f'date: {date_})\n')
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
                    width=Scalar(self.width, 'in'),
                    height=Scalar(self.height, 'in'))
        expr.to_string(self.writer)

    def get_image_magnification(self) -> float:
        return 1

    def option_scale_image(self) -> bool:
        return True

    def draw_image(self, gc: GraphicsContextBase, x: float, y: float,
                   im: ArrayLike, transform: Affine2DBase | None = None):
        h, w = im.shape[:2]
        if w == 0 or h == 0:
            return
        # TODO(@joneuhauser): Clips as soon as Typst supports them.
        # TODO(@joneuhauser): Links, Transforms (except translate).
        if transform is None:
            w = w / self.image_dpi
            h = h / self.image_dpi

        # TODO(@daskol): Do not flip ourselves. Let Typst flip it for us!
        img = ImageOps.flip(Image.fromarray(im))

        if self.config.detached_images:
            if self.basename is None:
                raise ValueError(
                    'Cannot save raster image files to filesystem since '
                    'target directory is not specified.')
            image_ext = f'.image{next(self._image_counter)}.png'
            image_path = self.path.with_suffix(image_ext)
            img.save(image_path)
            image = Call('image', f'"{image_path.name}"',
                         width=Scalar(w, 'in'), height=Scalar(h, 'in'))
        else:
            buf = BytesIO()
            img.save(buf, format='png')
            data = '"' + base64.b64encode(buf.getvalue()).decode('utf-8') + '"'
            image = Call('image.decode', Call('base64.decode', data),
                         format='"png"', width=Scalar(w, 'in'),
                         height=Scalar(h, 'in'))

        place = Call('place', image, dx=Scalar(x / self.dpi, 'in'),
                     dy=Scalar(self.height - y / self.dpi - h, 'in'))
        self.main.append(place)

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

        # Configure how to fill the path.
        fill = None
        if rgbFace is not None:
            fill = Call('rgb', *[Scalar(c * 100, '%') for c in rgbFace])

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
            if offset:
                stroke.kwargs.update({
                    'dash': Dictionary({
                        'array': bounds,
                        'phase': Scalar(offset, 'pt'),
                    })
                })
            else:
                stroke.kwargs.update({'dash': bounds})

        # Since Typst v0.13.0, path drawing API (aka curve) is more coherent to
        # Matplotlib's Path object.
        subpath: list[Call]
        superpath: list[list[Call]] = []
        for points, code in path.iter_segments(transform):
            points = normalize(points)
            scalars = tuple([Scalar(p, 'in') for p in points])
            match code:
                case Path.STOP:
                    raise NotImplementedError('It was previously ignored.')
                case Path.LINETO:
                    op = Call('curve.line', Array(scalars))
                case Path.MOVETO:
                    # NOTE There is no STOP opcode in Typst thus we should
                    # manually create subpaths.
                    subpath = []
                    superpath += [subpath]
                    op = Call('curve.move', Array(scalars))
                case Path.CURVE3:
                    qp1, qp2 = Array(scalars[:2]), Array(scalars[2:])
                    op = Call('curve.quad', qp1, qp2)
                case Path.CURVE4:
                    cp1 = Array(scalars[:2])
                    cp2 = Array(scalars[2:4])
                    cp3 = Array(scalars[4:6])
                    op = Call('curve.cubic', cp1, cp2, cp3)
                case Path.CLOSEPOLY:
                    op = Call('curve.close', mode='"straight"')
            subpath += [op]

        for subpath in superpath:
            line = Call('curve', *subpath, fill=fill, stroke=stroke)
            place = Call('place', line, dx=Scalar(0, 'in'), dy=Scalar(0, 'in'))
            self.main.append(place)

    def draw_quad_mesh(self, gc, master_transform, meshWidth, meshHeight,
                       coordinates, offsets, offsetTrans, facecolors,
                       antialiased, edgecolors):
        # TODO(@daskol): Apply offset transformation.
        vertices = np.array([master_transform.transform(point)
                             for point in coordinates])
        vertices /= self.dpi  # Points to inches.
        vertices[..., 1] = self.height - vertices[..., 1]  # Inverted Oy axis.

        # Cast coordinates to term in internal representation.
        shape = vertices.shape
        vertices = np.array([Scalar(el, 'in') for el in vertices.flatten()])
        vertices = vertices.reshape(shape)

        for i in range(vertices.shape[0] - 1):
            # TODO(@daskol): What about shapes coordinates, facecolors, and
            # edgecolors?
            facecolor = [Scalar(c * 100, '%') for c in facecolors[i]]
            for j in range(vertices.shape[1] - 1):
                # Create filling color.
                fill = Call('rgb', *facecolor)

                # Create stroke if line width is given.
                if edgecolors:
                    edgecolor = [Scalar(c * 100, '%') for c in edgecolors[i]]
                else:
                    edgecolor = facecolor
                stroke = None
                if (lw := gc.get_linewidth()) > 0:
                    paint = Call('rgb', *edgecolor)
                    stroke = Call('stroke', paint=paint,
                                  thickness=Scalar(lw, 'pt'))

                # TODO(@daskol): Take into account joints, dashes, and hatches.

                # Select quad and walk over it anti-clockwise.
                quad = vertices[i:i + 2, j:j + 2]
                quad = quad.reshape(4, 2)
                quad = quad[[2, 3, 1, 0]]
                line = Call('path', fill=fill, stroke=stroke, closed=True)
                for coords in quad:
                    point = Array(coords)
                    line.args.append(point)

                # Put on canvas with respect of the origin.
                place = Call('place', line,
                             dx=Scalar(0, 'in'), dy=Scalar(0, 'in'))
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
        return 1, 1

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

    fixed_dpi: Optional[float] = None

    manager_class = TypstFigureManager

    def draw(self):
        """Draw the figure using the renderer."""
        self.figure.draw_without_rendering()
        super().draw()

    def get_default_filetype(self):
        return 'typ'

    def print_pdf(self, filename, **kwargs):
        return self._print_as('pdf', filename, **kwargs)

    def print_png(self, filename, **kwargs):
        return self._print_as('png', filename, **kwargs)

    def print_svg(self, filename, **kwargs):
        return self._print_as('svg', filename, **kwargs)

    def print_typ(self, filename, *, bbox_inches_restore=None, metadata=None,
                  **kwargs):
        config = Config.from_dict(kwargs, drop=True, prefix='typst_')
        kwargs['bbox_inches_restore'] = bbox_inches_restore
        kwargs['metadata'] = metadata
        # Matplotlib shows quite unexpected behaviour. It renders the same
        # figure multiple types with rendering to temporary buffer (BytesIO)
        # rather than directly to file. So, we make rendering file-agnostic,
        # meaning that filename is an optional.
        if isinstance(filename, BytesIO):
            writer = getwriter('utf-8')(filename)
            self._print_typ(writer, config, **kwargs)
        else:
            with open(filename, 'w') as fout:
                self._print_typ(fout, config, pathlib.Path(filename), **kwargs)

    def _print_typ(self, buf: IO[str], config: Config,
                   path: pathlib.Path | None = None, /, metadata=None,
                   bbox_inches_restore=None, **kwargs):
        width, height = self.figure.get_size_inches()
        dpi = self.figure.dpi  # NOTE Do not enforce DPI!
        with TypstRenderer(self.figure, buf, config, path, metadata or {},
                           image_dpi=dpi) as tr:
            mmr = MixedModeRenderer(self.figure, width, height, dpi, tr,
                                    bbox_inches_restore=bbox_inches_restore)
            self.figure.draw(mmr)

    def _print_as(self, fmt, filename, *, metadata=None, **kwargs):
        # Set up default metadata. We use metadata as a condition for setting
        # canvas geometry in rendering.
        metadata = metadata or {}
        if 'author' not in metadata:
            metadata['author'] = 'mpl_typst (Typst Matplotlib backend)'

        with TemporaryDirectory(prefix='typst-', dir=get_cachedir()) as tmpdir:
            # Render figure in pure textual typst markup.
            inp_path = pathlib.Path(tmpdir) / 'main.typ'
            self.print_typ(inp_path, metadata=metadata, **kwargs)

            # Render typst markup running typst binary.
            out_path = inp_path.with_suffix(f'.{fmt}')
            dpi = kwargs.get('dpi', self.figure.dpi)
            cmd = [
                str(compiler), 'compile', f'--root={tmpdir}',
                f'--format={fmt}', '--diagnostic-format=short', f'--ppi={dpi}',
                str(inp_path), str(out_path)
            ]
            proc = subprocess.run(cmd, capture_output=True, cwd=tmpdir)
            if proc.returncode:
                kwargs = {'stdout': proc.stdout.decode('utf-8'),
                          'stderr': proc.stderr.decode('utf-8'),
                          'errors': []}
                for m in RE_ERROR.finditer(kwargs['stderr']):
                    error = m.groupdict()
                    error['line'] = int(error['line'])
                    error['column'] = int(error['column'])
                    kwargs['errors'].append(error)
                raise TypstRenderingError(**kwargs)

            # Move rendered figure from temporary directory to target location.
            if isinstance(filename, BytesIO):
                with open(out_path, 'rb') as fin:
                    copyfileobj(fin, filename)
            else:
                dst_path = pathlib.Path(filename)
                dst_path.parent.mkdir(exist_ok=True, parents=True)
                move(out_path, dst_path)


# Now, just provide the standard names that `backend.__init__` is expecting.
FigureCanvas = TypstFigureCanvas
FigureManager = TypstFigureManager

# Register file format for Typst markup.
register_backend('typ', 'mpl_typst', 'Typst markup')
