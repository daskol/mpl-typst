import warnings
from os import getenv
from pathlib import Path

PREFIX = 'MPL_TYPST_'


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
