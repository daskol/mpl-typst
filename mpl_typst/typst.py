from contextlib import contextmanager
from dataclasses import dataclass, field
from io import StringIO
from typing import Any, Literal, Self

__all__ = ('Array', 'Block', 'Content', 'Dictionary', 'Node', 'Scalar',
           'Writer')


class Writer:

    def __init__(self, buf: StringIO | None = None, indent: int = 0):
        self.buf = buf or StringIO()
        self.indent_ = indent
        self.indented = False

    @contextmanager
    def indent(self):
        self.indent_ += 1
        yield
        self.indent_ -= 1

    def to_string(self, value: Any) -> Self:
        match value:
            case Node():
                value.to_string(self)
            case bool():
                self.write(str(value).lower())
            case None:
                self.write('none')
            case _:
                self.write(str(value))
        return self

    def write(self, content: str):
        if not self.indented:
            self.indented = True
            self.buf.write(' ' * (2 * self.indent_))
        self.buf.write(content)

    def writeln(self, content: str | None = None):
        if content:
            self.write(content)
        self.buf.write('\n')
        self.indented = False


class Node:

    def __str__(self) -> str:
        buf = StringIO()
        self.to_string(buf)
        return buf.getvalue()

    def to_string(self, writer: Writer):
        raise NotImplementedError


Unit = Literal['pt', 'cm', 'mm', 'in', 'em', 'px', 'deg', 'rad', '%']


@dataclass
class Scalar(Node):

    value: float | int | str

    unit: Unit | None = None

    def __post_init__(self):
        if self.unit and isinstance(self.value, str):
            raise ValueError(
                f'String literals cannot have a unit: {self.unit}.')

    def to_string(self, writer: Writer):
        if self.unit:
            writer.write(f'{self.value}{self.unit}')
        elif isinstance(self.value, str):
            writer.write(f'"{self.value}"')
        else:
            writer.write(f'{self.value}')

@dataclass
class Content(Node):

    content: str

    def to_string(self, writer: Writer):
        writer.write('[')
        writer.write(self.content)
        writer.write(']')

@dataclass
class Array(Node):

    array: list[Any] = field(default_factory=list)

    def append(self, value):
        self.array.append(value)

    def to_string(self, writer: Writer, *, interior_only=False):
        if not interior_only:
            writer.write('(')
        for ix, item in enumerate(self.array):
            if ix > 0:
                if interior_only:
                    writer.writeln(',')  # Indentation in Call expression.
                else:
                    writer.write(', ')
            writer.to_string(item)
        if not interior_only:
            writer.write(')')


@dataclass
class Dictionary(Node):

    dictionary: dict[str, Any] = field(default_factory=dict)

    def to_string(self, writer: Writer, *, interior_only=False):
        if not interior_only:
            writer.write('(')
        for ix, (key, val) in enumerate(self.dictionary.items()):
            if ix > 0:
                if interior_only:
                    writer.writeln(',')  # Indentation in Call expression.
                else:
                    writer.write(', ')
            writer.write(f'{key}: ')
            writer.to_string(val)
        if not interior_only:
            writer.write(')')

    def update(self, items):
        self.dictionary.update(items)


@dataclass(init=False)
class Call(Node):

    name: str

    args: Array = field(default_factory=Array)

    kwargs: Array = field(default_factory=Dictionary)

    def __init__(self, name: str, *args, **kwargs):
        self.name = name
        self.args = Array([*args])
        self.kwargs = Dictionary(kwargs)

    def to_string(self, writer: Writer):
        writer.write(f'{self.name}(')
        with writer.indent():
            writer.writeln()
            self.args.to_string(writer, interior_only=True)
            if self.args.array and self.kwargs.dictionary:
                writer.writeln(',')
            self.kwargs.to_string(writer, interior_only=True)
        writer.write(')')


@dataclass
class Block(Node):

    exprs: list[Node] = field(default_factory=list)

    def append(self, expr: Node):
        self.exprs.append(expr)

    def to_string(self, writer: Writer):
        if not self.exprs:
            writer.write('{}')
            return

        writer.writeln('{')
        with writer.indent():
            for expr in self.exprs:
                expr.to_string(writer)
                writer.writeln()
        writer.write('}')
