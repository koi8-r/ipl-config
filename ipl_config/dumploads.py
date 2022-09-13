import io
import json
from contextlib import contextmanager
from ipaddress import IPv4Address
from os import PathLike
from pathlib import Path
from typing import IO, Any, Dict, Generator, Union, no_type_check  # noqa: I101

from typing_extensions import Protocol  # py38

from ._optional_libs import hcl2, toml, yaml


StrPathIO = Union[str, PathLike, IO, io.IOBase]


class ConfigLoadCallable(Protocol):  # pylint: disable=too-few-public-methods
    def __call__(self, f: StrPathIO, **kw: Any) -> Any:
        pass  # pragma: no cover


class ConfigLoadsCallable(Protocol):  # pylint: disable=too-few-public-methods
    def __call__(self, s: str, **kw: Any) -> Any:
        pass  # pragma: no cover


class ConfigDumpCallable(Protocol):  # pylint: disable=too-few-public-methods
    def __call__(self, obj: Dict[str, Any], f: StrPathIO, **kw: Any) -> None:
        pass  # pragma: no cover


class ConfigDumpsCallable(Protocol):  # pylint: disable=too-few-public-methods
    def __call__(self, obj: Dict[str, Any], **kw: Any) -> str:
        pass  # pragma: no cover


@contextmanager
def ensure_stream(
    stream: StrPathIO, write: bool = False
) -> Generator[Union[IO, io.IOBase], None, None]:
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
            obj, s, ensure_ascii=ensure_ascii, **kw  # type: ignore[arg-type]
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

# TODO: DELETEME
# class YamlDumper(yaml.SafeDumper):
#     pass
# YamlDumper.yaml_representers[IPv4Address] = lambda self, data: (
#     self.represent_str(str(data))
# )


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


def yaml_dumps(obj: Dict[str, Any], **kw: Any) -> str:
    sio = io.StringIO()
    yaml_dump(obj, sio, **kw)
    return sio.getvalue()


def yaml_load(f: StrPathIO, **_: Any) -> Any:
    with ensure_stream(f) as s:
        return yaml.load(s, yaml.SafeLoader)


def yaml_loads(s: str, **_: Any) -> Any:
    return yaml.load(s, yaml.SafeLoader)


# === TOML ===

# TODO: DELETEME
class TomlEncoder(toml.TomlEncoder):
    """
    This is example
    """

    @no_type_check
    def __init__(self, _dict=dict, preserve=False):
        super().__init__(_dict, preserve)
        # We can?: pydantic.json.ENCODERS_BY_TYPE ^ dump_funcs
        self.dump_funcs[IPv4Address] = lambda v: self.dump_funcs[str](str(v))


def toml_dump(obj: Dict[str, Any], f: StrPathIO, **kw: Any) -> None:
    # encoder = kw.pop('encoder', TomlEncoder(type(obj)))
    encoder = kw.pop('encoder', None)
    with ensure_stream(f, write=True) as s:
        toml.dump(obj, s, encoder=encoder)


def toml_dumps(obj: Dict[str, Any], **kw: Any) -> str:
    encoder = kw.pop('encoder', TomlEncoder(type(obj)))
    return toml.dumps(obj, encoder=encoder)


def toml_load(f: StrPathIO, **kw: Any) -> Any:
    with ensure_stream(f) as s:
        return toml.load(s, **kw)


def toml_loads(s: str, **kw: Any) -> Any:
    return toml.loads(s, **kw)


# === HCL2 ===


def hcl2_load(f: StrPathIO, **_: Any) -> Any:
    with ensure_stream(f) as s:
        return hcl2.load(s)


def hcl2_loads(s: str, **_: Any) -> Any:
    return hcl2.loads(s)
