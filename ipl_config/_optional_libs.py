from functools import wraps
from types import ModuleType
from typing import Any, Callable, Optional


try:
    import dotenv
except ImportError:
    dotenv: Optional[ModuleType] = None  # type: ignore[no-redef]

try:
    import yaml  # type: ignore[import]
except ImportError:
    yaml: Optional[ModuleType] = None  # type: ignore[no-redef]

try:
    import toml  # type: ignore[import]
except ImportError:
    toml: Optional[ModuleType] = None  # type: ignore[no-redef]


__all__ = (
    'dotenv',
    'yaml',
    'toml',
    'yaml_installed',
    'toml_installed',
)


def is_installed(name: str, val: ModuleType | None) -> Callable:
    if not val:
        raise ImportError(name + " is not installed")

    def deco(fn: Callable) -> Callable:
        @wraps(fn)
        def w(*a: Any, **kw: Any) -> Any:
            return fn(*a, **kw)

        return w

    return deco


def yaml_installed(fn: Callable) -> Callable:
    return is_installed('pyaml', yaml)(fn)


def toml_installed(fn: Callable) -> Callable:
    return is_installed('toml', yaml)(fn)
