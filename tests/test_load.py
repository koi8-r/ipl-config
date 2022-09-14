import io
import json
import os
from datetime import datetime
from ipaddress import IPv4Address
from pathlib import Path
from typing import List, Optional, Union
from unittest import mock

import pytest
from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module

from ipl_config import BaseSettings


class TcpTransport(BaseModel):  # pylint: disable=too-few-public-methods
    timeout: float
    buffer_size: int = Field(0.01, env='BUFF_size')


class Http(BaseModel):  # pylint: disable=too-few-public-methods
    host: str
    bind: str
    port: int
    interfaces: List[IPv4Address]
    transport: TcpTransport
    http2: bool = Field(env='HTTP_2')


class IplConfig(BaseSettings):  # pylint: disable=too-few-public-methods
    created: datetime
    version: str = 'v1'
    http_host: str = Field(deprecated=True)
    http: Http


@pytest.mark.parametrize(
    argnames=('env_file', 'conf_file'),
    argvalues=(
        ('tests/.env', 'examples/config_example.json'),
        ('tests/.env', 'examples/config_example.yaml'),
        ('tests/example.env', 'examples/config_example.toml'),
        ('tests/.env', 'examples/config_example.tf'),
    ),
)
def test_config_file(root_dir: Path, env_file: str, conf_file: str) -> None:
    with mock.patch.dict(
        os.environ,
        {
            'APP_CREATED': '2000-01-01T00:00:00Z',
            'app_http_bind': '0.0.0.0',
            'buff_size': '-1',
        },
    ):
        with pytest.warns(
            DeprecationWarning, match="'http_host' is deprecated"
        ):
            cfg = IplConfig(
                env_file=root_dir / env_file,
                config_file=root_dir / conf_file,
                version=999,
            )

        f = io.StringIO()
        cfg.write_json(f)

        actual = json.loads(f.getvalue())
        expected = {
            'created': '2000-01-01T00:00:00+00:00',
            'version': '999',
            'http_host': 'myname.lan',
            'http': {
                'host': 'myname.lan',
                'bind': '0.0.0.0',
                'interfaces': ['127.0.0.1', '192.168.0.1'],
                'port': 10001,
                'transport': {'timeout': 60.0, 'buffer_size': -1},
                'http2': True,
            },
        }
        assert actual == expected

        f.seek(0)
        f.truncate()
        cfg.write_schema(f)


def test_envs_case(root_dir: Path) -> None:
    class Bind(BaseModel):  # pylint: disable=too-few-public-methods
        host: str = Field(env='APP_HTTP_HOST')
        port: int

    class Config(BaseSettings):
        class Config:  # pylint: disable=too-few-public-methods
            case_sensitive = True
            env_prefix = 'APP'
            env_file = root_dir / 'tests/.env'

        http_2: bool = Field(env='h2')
        http: Bind = Field(env='Listen')

    with mock.patch.dict(
        os.environ,
        {
            'app_http_host': '0.0.0.0',
            'Listen_port': '3201',
            'APP_http_port': '1024',
            'h2': 'true',
            'H2': 'false',
        },
    ):
        cfg = Config()
        actual = cfg.dict()
        expected = {
            'http': {'host': 'myname.lan', 'port': 3201},
            'http_2': True,
        }
        assert actual == expected


def test_no_env_prefix() -> None:
    class Bind(BaseModel):  # pylint: disable=too-few-public-methods
        host: str

    class Config(BaseSettings):
        class Config:  # pylint: disable=too-few-public-methods
            env_prefix = None

        http_2: bool
        http: Bind

    with mock.patch.dict(
        os.environ, {'HTTP_HOST': '127.1.1.1', 'HTTP_2': 'false'}
    ):
        cfg = Config()
        actual = cfg.dict()
        expected = {'http': {'host': '127.1.1.1'}, 'http_2': False}
        assert actual == expected


def test_env_file() -> None:
    class Config(BaseSettings):
        class Config:  # pylint: disable=too-few-public-methods
            env_file = 'non_existing.env'

    with pytest.warns(
        UserWarning, match=f"'{Config.Config.env_file}' is not a file"
    ):
        Config()


def test_env_generics() -> None:
    from typing import Dict

    class Config(BaseSettings):
        ipv4: IPv4Address
        meta_r: dict
        meta: Dict[str, int]
        u_i: Union[float, int, str, None]
        u_d: Union[Dict[int, int], None]

    with mock.patch.dict(os.environ, {
        'APP_IPV4': '127.0.0.1',
        'app_meta_r_abc': '1x',
        'APP_META_Zz': '1',
        'APP_U_I': '123',
        'APP_U_D_99': '123',
    }):
        print()
        c = Config()
        print(c.json(indent=4))

        assert c.meta_r['abc'] == '1x'
        assert c.meta['zz'] == 1
        assert type(c.u_i) is float
        assert c.u_i == 123
        assert c.u_d == {99.0: 123}
