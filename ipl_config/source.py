# pylint: disable=no-name-in-module

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from os import PathLike
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple, Type, TypeVar
from warnings import warn

from pydantic import BaseModel
from pydantic.env_settings import InitSettingsSource
from pydantic.fields import SHAPE_SINGLETON, ModelField  # noqa: I101

import ipl_config  # pylint: disable=unused-import,cyclic-import  # noqa

from ._optional_libs import dotenv  # noqa: I202
from .dumploads import ConfigLoadCallable


S = TypeVar('S', bound='ipl_config.settings.BaseSettings')
SettingsStrategyCallable = Callable[[Type[S] | S], Dict[str, Any]]


# pylint: disable=too-few-public-methods
class EnvSettingsStrategy(object):
    __slots__ = (
        'env_prefix',
        'env_vars',
        'case_sensitive',
    )

    def __init__(
        self,
        env_prefix: Optional[str] = None,
        env_vars: Dict[str, Optional[str]] | None = None,
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

    def __call__(self, clazz: Type[S] | S) -> Dict[str, Any]:
        return self._from_env(clazz, self.env_prefix)

    def _from_env(
        self, clazz: Type[BaseModel] | BaseModel, prefix: Optional[str] = None
    ) -> Dict[str, Any]:
        prefix = prefix or ''
        result: Dict[str, Any] = {}

        field: ModelField
        for field in clazz.__fields__.values():
            extra = field.field_info.extra
            if extra.get('deprecated'):
                warn(f"{field.name} is deprecated", DeprecationWarning)

            env_name = extra.get('env')
            if not env_name:
                env_name = prefix + (prefix and '_' or '') + field.name
            if field.shape == SHAPE_SINGLETON and issubclass(
                field.type_, BaseModel
            ):
                env_val = self._from_env(field.type_, prefix=env_name)
            else:
                env_val = self.env_vars.get(  # type: ignore[assignment]
                    env_name if self.case_sensitive else env_name.lower(),
                )

            if env_val is not None:
                result[field.alias] = env_val

        return result


# pylint: disable=too-few-public-methods
class DotEnvSettingsStrategy(EnvSettingsStrategy):
    __slots__ = ()

    def __init__(
        self,
        env_prefix: Optional[str] = None,
        case_sensitive: Optional[bool] = False,
        env_file: Optional[str | PathLike] = None,
        env_file_encoding: Optional[str] = None,
    ):
        super().__init__(
            env_prefix=env_prefix,
            case_sensitive=case_sensitive,
            env_vars=read_env_file(
                env_file,
                encoding=env_file_encoding,
            )
            if env_file
            else {},
        )


# pylint: disable=too-few-public-methods
class KwSettingsStrategy(InitSettingsSource):
    def __init__(self, **kw: Any) -> None:
        super().__init__(init_kwargs=kw)


class FileSettingsStrategy(ABC):
    __slots__ = (
        'path',
        'config_format',
    )

    __extensions__: Tuple[str, ...] = ()

    def __init__(
        self,
        path: str | PathLike,
        config_format: Optional[str] = None,
    ):
        self.path: Path = Path(path).expanduser()
        self.config_format: Optional[str] = config_format

    def __call__(self, clazz: Type[S] | S) -> Dict[str, Any]:
        if not self.is_acceptable(self.path, self.config_format):
            return {}

        loader = self.get_loader(clazz)
        return loader(self.path)

    @abstractmethod
    def get_loader(self, clazz: Type[S] | S) -> ConfigLoadCallable:
        pass

    @classmethod
    def is_acceptable(
        cls,
        path: Optional[Path] = None,
        config_format: Optional[str] = None,
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
    __extensions__ = (
        'json',
        'js',
    )

    def get_loader(self, clazz: Type[S] | S) -> ConfigLoadCallable:
        return clazz.__config__.json_load


class YamlSettingsStrategy(FileSettingsStrategy):
    __extensions__ = (
        'yaml',
        'yml',
    )

    def get_loader(self, clazz: Type[S] | S) -> ConfigLoadCallable:
        return clazz.__config__.yaml_load


class TomlSettingsStrategy(FileSettingsStrategy):
    __extensions__ = (
        'toml',
        'tml',
    )

    def get_loader(self, clazz: Type[S] | S) -> ConfigLoadCallable:
        return clazz.__config__.toml_load


def read_env_file(
    path: str | PathLike,
    *,
    encoding: Optional[str] = None,
) -> Dict[str, Optional[str]]:
    path = Path(path).expanduser()
    is_env_default = str(path) == '.env'
    is_env_exists = path.is_file()

    if is_env_exists and not dotenv:
        warn('python-dotenv is not installed', ImportWarning)
    elif not is_env_exists and not is_env_default:
        warn(f"{path} is not a file", UserWarning)
    else:
        return dotenv.dotenv_values(path, encoding=encoding or 'utf-8')

    return {}
