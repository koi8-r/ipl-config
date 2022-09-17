# pylint: disable=no-name-in-module

from __future__ import annotations

import os
from abc import ABCMeta, abstractmethod
from os import PathLike
from pathlib import Path
from types import ModuleType
from typing import (  # noqa: I101
    TYPE_CHECKING,
    Any,
    ClassVar,
    Dict,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    no_type_check,
)
from warnings import warn

import pydantic
from pydantic import BaseModel
from pydantic.env_settings import InitSettingsSource
from pydantic.fields import ModelField
from pydantic.typing import get_origin, is_union
from pydantic.utils import lenient_issubclass

from ._optional_libs import dotenv  # noqa: I202
from ._optional_libs import hcl2, toml, yaml
from .dumploads import (
    ConfigLoadCallable,
    hcl2_load,
    json_load,
    toml_load,
    yaml_load,
)


if TYPE_CHECKING:
    from ipl_config import BaseSettings  # pragma: no cover


class SettingsStrategyMetaclass(ABCMeta):  # noqa: B024
    @no_type_check
    def __call__(cls, *args, **kwargs):
        """
        Ensure the class has all its dependencies during constructor
        without needs to call to `super`
        """
        for dep in getattr(cls, '__dependencies__', None) or ():
            if isinstance(dep, Exception):
                raise dep
        return super().__call__(*args, **kwargs)


# type: ignore[too-few-public-methods]
# pylint: disable=too-few-public-methods
class SettingsStrategy(metaclass=SettingsStrategyMetaclass):
    __dependencies__: ClassVar[
        Optional[Sequence[Union[ModuleType, ImportError]]]
    ] = None

    @abstractmethod
    def __call__(
        self, clazz: Union[Type[BaseSettings], BaseSettings]
    ) -> Dict[str, Any]:
        pass  # pragma: no cover


# pylint: disable=too-few-public-methods
class EnvSettingsStrategy(SettingsStrategy):
    __slots__ = 'env_prefix', 'env_vars', 'case_sensitive'

    def __init__(
        self,
        env_prefix: Optional[str] = None,
        env_vars: Union[Dict[str, Optional[str]], None] = None,
        case_sensitive: Optional[bool] = False,
    ):
        self.env_prefix: Optional[str] = env_prefix
        self.env_vars: Dict[str, Optional[str]] = (
            env_vars  # type: ignore[assignment]
            if env_vars is not None
            else os.environ
        )
        self.case_sensitive: Optional[bool] = case_sensitive

        # self.env_vars: Dict[str, Optional[str]] = {
        #     **os.environ,
        #     **(read_env_file(
        #         env_file, encoding=env_file_encoding
        #     ) if env_file else {}),
        # }

        if not case_sensitive:
            if env_prefix:
                self.env_prefix = env_prefix.lower()
            self.env_vars = {k.lower(): v for k, v in self.env_vars.items()}

    def __call__(
        self,
        clz: Union[Type[BaseModel], BaseModel],
        prefix: Optional[str] = None,
    ) -> Dict[str, Any]:
        if prefix is None:
            prefix = self.env_prefix

        return dict(
            filter(
                lambda x: x is not None,  # type: ignore
                (
                    self._get_env_val(clz=clz, field=f, prefix=prefix)
                    for f in clz.__fields__.values()
                ),
            )
        )

    def _get_env_val(  # pylint: disable=too-many-branches
        self,
        clz: Union[Type[BaseModel], BaseModel],
        field: ModelField,
        prefix: Optional[str] = None,
    ) -> Optional[Tuple[str, Any]]:
        prefix = prefix or ''

        if field.field_info.extra.get('deprecated'):
            warn(f"{field.name!r} is deprecated", DeprecationWarning)
        if field.has_alias:
            warn('Instead of aliases use the `env` setting', FutureWarning)

        env_name = field.field_info.extra.get('env')
        if not env_name:
            env_name = prefix + (prefix and '_' or '') + field.name
        if self.case_sensitive:
            env_name = env_name.lower()

        env_val: Any = self.env_vars.get(env_name)

        if (
            field.shape == pydantic.fields.SHAPE_SINGLETON
            and lenient_issubclass(field.type_, BaseModel)  # noqa: W503
        ):
            env_val = self(field.type_, prefix=env_name)
        elif field.is_complex():
            if env_val is not None:
                env_val = clz.__config__.json_loads(env_val)
        elif is_union(get_origin(field.type_)):
            for f in field.sub_fields:
                try:
                    if env_val is not None and f.is_complex():
                        env_val = clz.__config__.json_loads(env_val)
                    else:
                        break
                except ValueError:
                    pass

        if env_val is not None:
            return field.alias, env_val

        return None


# pylint: disable=too-few-public-methods
class DotEnvSettingsStrategy(EnvSettingsStrategy):
    __slots__ = ()

    def __init__(
        self,
        env_prefix: Optional[str] = None,
        case_sensitive: Optional[bool] = False,
        env_file: Union[str, PathLike, None] = None,
        env_file_encoding: Optional[str] = None,
    ):
        super().__init__(
            env_prefix=env_prefix,
            case_sensitive=case_sensitive,
            env_vars=read_env_file(env_file, encoding=env_file_encoding)
            if env_file
            else {},
        )


# pylint: disable=too-few-public-methods
class KwSettingsStrategy(SettingsStrategy, InitSettingsSource):
    def __call__(
        self, clazz: Union[Type[BaseSettings], BaseSettings]
    ) -> Dict[str, Any]:
        return self.init_kwargs

    def __init__(self, **kw: Any) -> None:
        super().__init__(init_kwargs=kw)


class FileSettingsStrategy(SettingsStrategy):
    __slots__ = 'path', 'config_format'

    __extensions__: ClassVar[Sequence[str]] = ()

    def __init__(
        self, path: Union[str, PathLike], config_format: Optional[str] = None
    ):
        self.path: Path = Path(path).expanduser()
        self.config_format: Optional[str] = config_format

    def __call__(
        self, clazz: Union[Type[BaseSettings], BaseSettings]
    ) -> Dict[str, Any]:
        if not self.is_acceptable(self.path, self.config_format):
            return {}

        loader = self.get_loader(clazz)
        return loader(self.path)

    @abstractmethod
    def get_loader(
        self, clazz: Union[Type[BaseSettings], BaseSettings]
    ) -> ConfigLoadCallable:
        pass  # pragma: no cover

    @classmethod
    def is_acceptable(
        cls, path: Optional[Path] = None, config_format: Optional[str] = None
    ) -> bool:
        """
        :return: True if format is acceptable to loads
        """
        if path is None:
            return False

        if config_format is None:
            config_format = cls.detect_format(path)

        return bool(config_format and config_format in cls.__extensions__)

    @classmethod
    def detect_format(cls, path: Path) -> Optional[str]:
        return path.suffix[1:]


class JsonSettingsStrategy(FileSettingsStrategy):
    __extensions__ = 'json', 'js'

    def get_loader(
        self, clazz: Union[Type[BaseSettings], BaseSettings]
    ) -> ConfigLoadCallable:
        return json_load


class YamlSettingsStrategy(FileSettingsStrategy):
    __dependencies__ = (yaml,)
    __extensions__ = 'yaml', 'yml'

    def get_loader(
        self, clazz: Union[Type[BaseSettings], BaseSettings]
    ) -> ConfigLoadCallable:
        return yaml_load


class TomlSettingsStrategy(FileSettingsStrategy):
    __dependencies__ = (toml,)
    __extensions__ = 'toml', 'tml'

    def get_loader(
        self, clazz: Union[Type[BaseSettings], BaseSettings]
    ) -> ConfigLoadCallable:
        return toml_load


class Hcl2SettingsStrategy(FileSettingsStrategy):
    __dependencies__ = (hcl2,)
    __extensions__ = 'hcl', 'hcl2', 'tf'

    def get_loader(
        self, clazz: Union[Type[BaseSettings], BaseSettings]
    ) -> ConfigLoadCallable:
        return hcl2_load


def read_env_file(
    path: Union[str, PathLike], *, encoding: Optional[str] = None
) -> Dict[str, Optional[str]]:
    path = Path(path).expanduser()
    is_env_default = str(path) == '.env'
    is_env_exists = path.is_file()

    if is_env_exists and isinstance(dotenv, Exception):
        warn(str(dotenv), ImportWarning)
    elif not is_env_exists and not is_env_default:
        warn(f"{str(path)!r} is not a file", UserWarning)
    else:
        return dotenv.dotenv_values(path, encoding=encoding or 'utf-8')

    return {}
