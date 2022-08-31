import os
from contextlib import contextmanager
from typing import Generator, Mapping, MutableMapping, Optional


@contextmanager
def environ(
    new_env: Mapping[str, str]
) -> Generator[MutableMapping[str, Optional[str]], None, None]:
    old_env = os.environ.copy()
    os.environ.update(new_env)
    yield os.environ  # type: ignore[misc]
    os.environ.clear()
    os.environ.update(old_env)
