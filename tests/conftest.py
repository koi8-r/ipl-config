from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def root_dir(pytestconfig) -> Path:  # type: ignore[no-untyped-def]
    return pytestconfig.rootpath
