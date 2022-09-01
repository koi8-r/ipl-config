import io
import json
from datetime import datetime
from ipaddress import IPv4Address
from pathlib import Path

import pytest
from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module

from ipl_config import BaseSettings

from .utils import environ  # noqa: I202


class TcpTransport(BaseModel):  # pylint: disable=too-few-public-methods
    timeout: float
    buffer_size: int = Field(0.01, env='BUFF_size')


class Http(BaseModel):  # pylint: disable=too-few-public-methods
    host: str
    bind: str
    port: int
    interfaces: list[IPv4Address]
    transport: TcpTransport
    http2: bool = Field(env='HTTP_2')


class IplConfig(BaseSettings):  # pylint: disable=too-few-public-methods
    created: datetime
    version: str = 'v1'
    http_host: str
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
    with environ(
        {
            'APP_CREATED': '2000-01-01T00:00:00Z',
            'app_http_bind': '0.0.0.0',
            'buff_size': '-1',
        }
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
