import warnings
from dataclasses import dataclass, fields
from os import PathLike, getenv
from pathlib import Path
from sys import version_info
from typing import IO, Any

if version_info >= (3, 11):
    from tomli import load as load_toml
    from typing_extensions import Self
else:
    from typing import Self

    from toml import load as load_toml

PREFIX = 'MPL_TYPST_'


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
        if not path.exists() or not path.is_file:
            warnings.warn(f'No typst compiler is not found at {path}.',
                          RuntimeWarning)
    else:
        for bin_dir in getenv('PATH', '').split(':'):
            if (bin_dir / default).exists():
                path = (bin_dir / default).expanduser()
                break
        else:
            warnings.warn(('Typst compiler found at `PATH` envvar. Consider '
                           '`MPL_TYPST_COMPILER` envvar to set path to typst '
                           'compiler explicitely.'), RuntimeWarning)
            return default
    return path.absolute()


compiler = get_typst_compiler('compiler')  # MPL_TYPST_COMPILER
