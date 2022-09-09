import json

from pydantic import BaseModel  # pylint: disable=no-name-in-module

from ipl_config import BaseSettings
from ipl_config.dumploads import json_dumps, yaml_dumps, yaml_loads


class Http(BaseModel):  # pylint: disable=too-few-public-methods
    listen: str


class Config(BaseSettings):
    http: Http
    port: int
    host: str


cfg = Config(host='127.0.0.1', port=1024, http={'listen': '0.0.0.0:4511'})
expected = {
    'host': '127.0.0.1',
    'port': 1024,
    'http': {'listen': '0.0.0.0:4511'},
}


def test_to_env() -> None:
    assert cfg.to_env() == {
        'APP_HTTP_LISTEN': '0.0.0.0:4511',
        'APP_HOST': '127.0.0.1',
        'APP_PORT': '1024',
    }


def test_json_dumps() -> None:
    assert json.loads(json_dumps(cfg.dict())) == expected


def test_yaml_dumps() -> None:
    assert yaml_loads(yaml_dumps(cfg.dict())) == expected
