[![tests](https://github.com/koi8-r/ipl-config/actions/workflows/ci.yml/badge.svg)](https://github.com/koi8-r/ipl-config/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/koi8-r/ipl-config/branch/master/graph/badge.svg?token=OKURU75Y7A)](https://codecov.io/gh/koi8-r/ipl-config)
[![pypi](https://img.shields.io/pypi/v/ipl-config.svg)](https://pypi.python.org/pypi/ipl-config)
[![versions](https://img.shields.io/pypi/pyversions/ipl-config.svg)](https://github.com/koi8-r/ipl-config)


# Config adapters with pydantic behavior
- json
- yaml
- toml
- hcl2
- environ
- .env
- TODO: multiline PEM keys load with cryptography

## Examples
### .env
```dotenv
APP_VERSION=v0.0.1a1
APP_HTTP_HOST=myname.lan
HTTP_2=true
APP_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQg8M4vd2AmKTW0/nqc
YQBi/bRZjkVezdGHi+zH5kYvm/2hRANCAATxEs1e8hqwpYCTk3amfq/UnGyvViPZ
Midz4nFzQvcq7A9Ju/wvEfLDjA131kh2Sk+x3dgLxhTf7yKJXZC0jg3d
-----END PRIVATE KEY-----"
```
### config.yaml
```yaml
http:
  port: 10001
  transport:
    timeout: 60.0
    buffer_size: 65535
  interfaces:
    - 127.0.0.1
    - 192.168.0.1
version: 1
```
### yaml with env, dotenv and args overrides
```python
from datetime import datetime
from ipaddress import IPv4Address
from os import environ
from pathlib import Path

from pydantic import BaseModel, Field

from ipl_config import BaseSettings


class TcpTransport(BaseModel):
    timeout: float  # from config file
    buffer_size: int = Field(0.01, env='BUFF_SIZE')  # from env


class Http(BaseModel):
    host: str  # from dotenv
    bind: str  # from env
    port: int  # from config file
    interfaces: list[IPv4Address]  # from config file
    transport: TcpTransport
    http2: bool = Field(env='HTTP_2')  # from dotenv


class IplConfig(BaseSettings):
    version: str  # from kwargs
    created: datetime  # from env
    http: Http  # env also works for complex objects
    private_key: str  # from dotenv


if __name__ == "__main__":
    environ['app_http_bind'] = '1.1.1.1'
    environ['buff_size'] = '-1'
    environ['app_created'] = '2000-01-01T00:00:00Z'

    root = Path('.')

    cfg = IplConfig(
        version='v0.0.1a1',
        env_file=root / '.env',
        config_file=root / 'config.yaml',
    )
    cfg.write_json(indent=4)
    print()
```
