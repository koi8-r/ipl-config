import pytest

from ipl_config.source import JsonSettingsStrategy


class SettingsStrategy(JsonSettingsStrategy):
    __dependencies__ = (ImportError('not installed'),)


def test_missed_dependency() -> None:
    with pytest.raises(ImportError):
        SettingsStrategy(path='file.json')
