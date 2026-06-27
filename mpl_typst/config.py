import re
import subprocess
import warnings
from dataclasses import dataclass, fields
from functools import total_ordering
from os import PathLike, getenv
from pathlib import Path
from sys import version_info
from typing import IO, Any

if version_info >= (3, 11):
    from tomllib import load as load_toml
    from typing import Self
else:
    from tomli import load as load_toml
    from typing_extensions import Self

PREFIX = 'MPL_TYPST_'

SEMVER_PATTERN = (
    r'(?P<major>0|[1-9]\d*)\.'
    r'(?P<minor>0|[1-9]\d*)\.'
    r'(?P<patch>0|[1-9]\d*)'
    r'(?:-(?P<prerelease>'
    r'(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)'
    r'(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*'
    r'))?'
    r'(?:\+(?P<build>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?'
)

TYPST_COMPILER_VERSION_RE = re.compile(
    rf'^typst\s+(?P<version>{SEMVER_PATTERN})(?:\s+\((?P<revision>[^)]+)\))?$')


@total_ordering
@dataclass(frozen=True, slots=True, eq=False)
class TypstVersion:
    """Semantic Typst compiler version."""

    major: int

    minor: int

    patch: int

    prerelease: tuple[int | str, ...] = ()

    build: str = ''

    revision: str | None = None

    @classmethod
    def from_match(cls, match: re.Match[str]) -> Self:
        prerelease = match.group('prerelease') or ''
        prerelease_parts: list[int | str, ...] = []
        for part in prerelease.split('.'):
            if not part:
                continue
            if part.isdecimal():
                prerelease_parts.append(int(part))
            else:
                prerelease_parts.append(part)

        return cls(
            major=int(match.group('major')),
            minor=int(match.group('minor')),
            patch=int(match.group('patch')),
            prerelease=tuple(prerelease_parts),
            build=match.group('build') or '',
            revision=match.groupdict().get('revision'),
        )

    @property
    def release(self) -> tuple[int, int, int]:
        return self.major, self.minor, self.patch

    def __str__(self) -> str:
        version = f'{self.major}.{self.minor}.{self.patch}'
        if self.prerelease:
            version += '-' + '.'.join(str(part) for part in self.prerelease)
        if self.build:
            version += f'+{self.build}'
        return version

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TypstVersion):
            return NotImplemented
        return (self.release,
                self.prerelease) == (other.release, other.prerelease)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, TypstVersion):
            return NotImplemented
        if self.release != other.release:
            return self.release < other.release
        return self._compare_prerelease(self.prerelease, other.prerelease) < 0

    @staticmethod
    def _compare_prerelease(lhs: tuple[int | str, ...],
                            rhs: tuple[int | str, ...],) -> int:
        if not lhs and not rhs:
            return 0
        if not lhs:
            return 1
        if not rhs:
            return -1

        for left, right in zip(lhs, rhs):
            if left == right:
                continue
            if isinstance(left, int) and isinstance(right, str):
                return -1
            if isinstance(left, str) and isinstance(right, int):
                return 1
            return 1 - 2 * int(left < right)  # {-1, 1}

        return (len(lhs) > len(rhs)) - (len(lhs) < len(rhs))


@dataclass(slots=True)
class Config:
    """Typst renderer configuration."""

    preamble: str = ''

    detached_images: bool = False

    @classmethod
    def from_dict(cls, obj: dict[str, Any], drop=False, prefix='') -> Self:
        input_keys: set[str] = set()
        prefix_len = len(prefix)
        for key in obj.keys():
            if not prefix:
                input_keys.add(key)
            elif prefix and key.startswith(prefix):
                input_keys.add(key[prefix_len:])
        valid_keys = {f.name for f in fields(cls)}
        kwargs = {k: obj[f'{prefix}{k}'] for k in valid_keys & input_keys}
        if drop:
            for key in input_keys - valid_keys:
                obj.pop(f'{prefix}{key}')
        return cls(**kwargs)

    @classmethod
    def from_toml(cls, path: PathLike | IO[bytes] | str) -> Self:
        if isinstance(path, str | PathLike):
            with open(path, 'rb') as fin:
                return cls.from_toml(fin)
        else:
            return cls.from_dict(load_toml(path))


def get_typst_compiler(name: str, default=Path('typst')) -> Path:
    if (envvar := getenv(f'{PREFIX}{name.upper()}')) is not None:
        path = Path(envvar).expanduser()
        if not path.exists() or not path.is_file():
            warnings.warn(f'No typst compiler is not found at {path}.',
                          RuntimeWarning)
    else:
        for bin_dir in getenv('PATH', '').split(':'):
            if (Path(bin_dir) / default).exists():
                path = (Path(bin_dir) / default).expanduser()
                break
        else:
            warnings.warn(('No Typst compiler found in `PATH` envvar. '
                           'Consider `MPL_TYPST_COMPILER` envvar to set path '
                           'to typst compiler explicitly.'), RuntimeWarning)
            return default
    return path.absolute()


def get_typst_compiler_version(path: Path) -> TypstVersion | None:
    cmd = (str(path), '--version')
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except OSError:
        return None
    if proc.returncode:
        return None
    return parse_typst_compiler_version(proc.stdout)


def parse_typst_compiler_version(output: str) -> TypstVersion | None:
    match = TYPST_COMPILER_VERSION_RE.match(output.strip())
    if match is None:
        return None
    try:
        return TypstVersion.from_match(match)
    except ValueError:
        return None


compiler = get_typst_compiler('compiler')  # MPL_TYPST_COMPILER
compiler_version = get_typst_compiler_version(compiler)
