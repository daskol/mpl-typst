from dataclasses import dataclass, fields
from os import PathLike
from sys import version_info
from typing import IO, Any

if version_info >= (3, 11):
    from tomli import load as load_toml
    from typing_extensions import Self
else:
    from typing import Self

    from toml import load as load_toml


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
