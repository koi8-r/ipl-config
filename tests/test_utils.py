from copy import copy

from ipl_config.utils import LowerCaseDict


def test_lower_dict() -> None:
    d = LowerCaseDict({'A': 'a'}, x='x', Z='z', e=0)
    d['I'] = 1
    del d['E']

    assert copy(d) == {'a': 'a', 'x': 'x', 'z': 'z', 'i': 1}
    assert len(d) == 4
    assert repr(d) == "LowerCaseDict({'a': 'a', 'x': 'x', 'z': 'z', 'i': 1})"
    assert repr(d) == str(d)
