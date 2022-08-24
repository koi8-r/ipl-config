import io
import json
from contextlib import contextmanager
from os import PathLike
from pathlib import Path
from typing import IO, Any, Dict, Generator, Protocol  # noqa: I101

from ._optional_libs import toml, toml_installed, yaml, yaml_installed


StrPathIO = str | PathLike | IO | io.IOBase


class ConfigLoadCallable(Protocol):  # pylint: disable=too-few-public-methods
    def __call__(self, f: StrPathIO, **kw: Any) -> Any:
        pass


class ConfigLoadsCallable(Protocol):  # pylint: disable=too-few-public-methods
    def __call__(self, s: str, **kw: Any) -> Any:
        pass


class ConfigDumpCallable(Protocol):  # pylint: disable=too-few-public-methods
    def __call__(self, obj: Dict[str, Any], f: StrPathIO, **kw: Any) -> None:
        pass


class ConfigDumpsCallable(Protocol):  # pylint: disable=too-few-public-methods
    def __call__(self, obj: Dict[str, Any], **kw: Any) -> str:
        pass


@contextmanager
def ensure_stream(
    stream: StrPathIO,
    write: bool = False,
) -> Generator[IO | io.IOBase, None, None]:
    if isinstance(stream, io.IOBase):
        yield stream
    else:
        f = io.open(
            Path(stream).expanduser(),  # type: ignore[arg-type]
            (write and 'w' or 'r') + 't',
            encoding='utf-8',
            errors='surrogateescape',
        )
        yield f
        f.close()


# === JSON ===


def json_dump(obj: Dict[str, Any], f: StrPathIO, **kw: Any) -> None:
    ensure_ascii = kw.pop('ensure_ascii', False)
    with ensure_stream(f, write=True) as s:
        json.dump(
            obj,
            s,  # type: ignore[arg-type]
            ensure_ascii=ensure_ascii,
            **kw,
        )


def json_dumps(obj: Dict[str, Any], **kw: Any) -> str:
    sio = io.StringIO()
    json_dump(obj, sio, **kw)
    return sio.getvalue()


def json_load(f: StrPathIO, **kw: Any) -> Any:
    with ensure_stream(f) as s:
        return json.load(s, **kw)


def json_loads(s: str, **kw: Any) -> Any:
    return json.loads(s, **kw)


# === YAML ===


@yaml_installed
def yaml_dump(obj: Dict[str, Any], f: StrPathIO, **kw: Any) -> None:
    allow_unicode = kw.pop('allow_unicode', True)
    encoding = kw.pop('encoding', 'utf-8')

    with ensure_stream(f, write=True) as s:
        yaml.dump(
            obj,
            s,
            yaml.SafeDumper,
            allow_unicode=allow_unicode,
            encoding=encoding,
            **kw,
        )


@yaml_installed
def yaml_dumps(obj: Dict[str, Any], **kw: Any) -> str:
    sio = io.StringIO()
    yaml_dump(obj, sio, **kw)
    return sio.getvalue()


@yaml_installed
def yaml_load(f: StrPathIO, **_: Any) -> Any:
    with ensure_stream(f) as s:
        return yaml.load(s, yaml.SafeLoader)


@yaml_installed
def yaml_loads(s: str, **_: Any) -> Any:
    return yaml.load(s, yaml.SafeLoader)


# === TOML ===


@toml_installed
def toml_dump(obj: Dict[str, Any], f: StrPathIO, **kw: Any) -> None:
    with ensure_stream(f, write=True) as s:
        toml.dump(obj, s, **kw)


@toml_installed
def toml_dumps(obj: Dict[str, Any], **kw: Any) -> str:
    return toml.dumps(obj, **kw)


@toml_installed
def toml_load(f: StrPathIO, **kw: Any) -> Any:
    with ensure_stream(f) as s:
        return toml.load(s, **kw)


@toml_installed
def toml_loads(s: str, **kw: Any) -> Any:
    return toml.loads(s, **kw)
