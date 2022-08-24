from datetime import datetime
from ipaddress import IPv4Address
from os import environ
from pathlib import Path

from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module

from ipl_config import BaseSettings


class TcpTransport(BaseModel):  # pylint: disable=too-few-public-methods
    timeout: float  # from config file
    buffer_size: int = Field(0.01, env='BUFF_SIZE')  # from env


class Http(BaseModel):  # pylint: disable=too-few-public-methods
    host: str  # from dotenv
    bind: str  # from env
    port: int  # from config file
    interfaces: list[IPv4Address]  # from config file
    transport: TcpTransport
    http2: bool = Field(env='HTTP_2')  # from dotenv


class IplConfig(BaseSettings):  # pylint: disable=too-few-public-methods
    version: str  # from kwargs
    created: datetime  # from env
    http: Http


if __name__ == "__main__":
    environ['app_http_bind'] = '1.1.1.1'
    environ['buff_size'] = '-1'
    environ['app_created'] = '2000-01-01T00:00:00Z'

    root = Path('../')

    cfg = IplConfig(
        version='v0.0.1a1',
        env_file=root / 'tests' / '.env',
        config_file=root / 'examples' / 'config_example.yaml',
    )
    cfg.write_json(indent=4)
    print()
