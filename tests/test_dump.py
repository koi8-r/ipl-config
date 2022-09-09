from pydantic import BaseModel  # pylint: disable=no-name-in-module

from ipl_config import BaseSettings


def test_to_env() -> None:
    class Http(BaseModel):  # pylint: disable=too-few-public-methods
        listen: str

    class Config(BaseSettings):
        http: Http
        port: int
        host: str

    cfg = Config(host='127.0.0.1', port=1024, http={'listen': '0.0.0.0:4511'})
    assert cfg.to_env() == {
        'APP_HTTP_LISTEN': '0.0.0.0:4511',
        'APP_HOST': '127.0.0.1',
        'APP_PORT': '1024',
    }
