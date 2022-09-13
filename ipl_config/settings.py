# pylint: disable=no-name-in-module

import sys
from collections import OrderedDict
from decimal import Decimal
from os import PathLike
from pathlib import Path
from typing import (
    AbstractSet,
    Any,
    ClassVar,
    Dict,
    Generator,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
)

from pydantic import BaseConfig, BaseModel
from pydantic.config import Extra
from pydantic.utils import deep_update

from .dumploads import StrPathIO, json_dump, toml_dump, yaml_dump
from .source import (
    DotEnvSettingsStrategy,
    EnvSettingsStrategy,
    Hcl2SettingsStrategy,
    JsonSettingsStrategy,
    KwSettingsStrategy,
    SettingsStrategyCallable,
    TomlSettingsStrategy,
    YamlSettingsStrategy,
)


IntStr = Union[int, str]
AbstractSetIntStr = AbstractSet[IntStr]
MappingIntStrAny = Mapping[IntStr, Any]
TupleGenerator = Generator[Tuple[str, Any], None, None]


class BaseSettings(BaseModel):
    __slots__ = ()

    class Config(BaseConfig):  # pylint: disable=too-few-public-methods
        env_prefix: Optional[str] = 'APP'
        env_file: Union[str, PathLike, None] = '.env'
        env_file_encoding: Optional[str] = None
        case_sensitive: bool = False
        validate_all: bool = True
        extra: Extra = Extra.ignore
        arbitrary_types_allowed = True

    __config__: ClassVar[Type[Config]] = Config

    def __init__(  # pylint: disable=too-many-arguments
        self,
        env_prefix: Optional[str] = None,
        env_file: Union[str, PathLike, None] = None,
        config_file: Union[str, PathLike, None] = None,
        config_format: Optional[str] = None,
        source_strategies: Optional[Sequence[SettingsStrategyCallable]] = None,
        **kw: Any,
    ) -> None:
        if config_file is not None:
            config_file = Path(config_file)

        if source_strategies is None:
            cfg = self.__config__
            source_strategies = [
                KwSettingsStrategy(**kw),
                EnvSettingsStrategy(
                    env_prefix=env_prefix or cfg.env_prefix,
                    case_sensitive=cfg.case_sensitive,
                ),
                DotEnvSettingsStrategy(
                    env_prefix=env_prefix or cfg.env_prefix,
                    env_file=env_file or cfg.env_file,
                    env_file_encoding=cfg.env_file_encoding,
                    case_sensitive=cfg.case_sensitive,
                ),
            ]
            if config_file:
                for s in (
                    JsonSettingsStrategy,
                    YamlSettingsStrategy,
                    TomlSettingsStrategy,
                    Hcl2SettingsStrategy,
                ):
                    if s.is_acceptable(config_file, config_format):
                        source_strategies.append(
                            s(
                                config_file,
                                config_format,  # type: ignore[abstract]
                            )
                        )
                        break
                else:
                    raise NotImplementedError(
                        f"No readers found for the config file: {config_file}"
                    )

        super().__init__(
            **deep_update(*reversed([s(self) for s in source_strategies]))
        )

    def safe_dict(
        self,
        *,
        include: Optional[Union[AbstractSetIntStr, MappingIntStrAny]] = None,
        exclude: Optional[Union[AbstractSetIntStr, MappingIntStrAny]] = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> Dict[str, Any]:
        return dict(
            self.safe_iter(
                to_dict=True,
                by_alias=by_alias,
                include=include,
                exclude=exclude,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                exclude_none=exclude_none,
            )
        )

    def safe_iter(  # pylint: disable=too-many-arguments
        self,
        to_dict: bool = False,
        by_alias: bool = False,
        include: Optional[Union[AbstractSetIntStr, MappingIntStrAny]] = None,
        exclude: Optional[Union[AbstractSetIntStr, MappingIntStrAny]] = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> TupleGenerator:
        for k, v in super()._iter(
            to_dict,
            by_alias,
            include,
            exclude,
            exclude_unset,
            exclude_defaults,
            exclude_none,
        ):
            try:
                v = self.__json_encoder__(v)
            except TypeError:
                pass
            yield k, v,

    def _write_json(self, o: Dict[str, Any], f: StrPathIO, **kw: Any) -> None:
        # take encoder from `self.__config__.json_encoders`
        encoder = kw.pop('default', self.__json_encoder__)
        json_dump(o, f, default=encoder, **kw)

    def write_schema(self, f: StrPathIO = sys.stdout, **kw: Any) -> None:
        return self._write_json(self.schema(), f, **kw)

    def write_json(self, f: StrPathIO = sys.stdout, **kw: Any) -> None:
        return self._write_json(self.dict(), f, **kw)

    def write_toml(self, f: StrPathIO = sys.stdout, **kw: Any) -> None:
        return toml_dump(self.safe_dict(), f, **kw)

    def write_yaml(self, f: StrPathIO = sys.stdout, **kw: Any) -> None:
        return yaml_dump(self.safe_dict(), f, **kw)

    def to_env(self, **kw: Any) -> Dict[str, str]:
        prefix = self.__config__.env_prefix
        if not prefix:
            return self._to_env(self.dict(**kw))
        return self._to_env(self.dict(**kw), prefix)

    def _to_env(self, ns: Dict[str, Any], *path: str) -> Dict[str, str]:
        res = OrderedDict()

        for name, model in ns.items():
            _path = path + (name,)
            env_name = '_'.join(_.upper() for _ in _path)

            if not isinstance(model, dict):
                # for mypy
                env_val: Union[bool, bytes, str, int, float, complex, Decimal]
                if model is None:
                    env_val = ''
                elif isinstance(model, bool):
                    env_val = int(model)
                elif isinstance(model, bytes):
                    env_val = model.decode(
                        encoding='utf-8', errors='surrogateescape'
                    )
                elif isinstance(model, (str, int, float, complex, Decimal)):
                    env_val = model
                else:
                    raise NotImplementedError(
                        f"Not a scalar: {env_name}={type(model)}"
                    )

                res[env_name] = str(env_val)
            else:
                for k, v in self._to_env(model, *_path).items():
                    res[k] = v

        return res
