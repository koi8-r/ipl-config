from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any, AnyStr, Iterator, Optional


class LowerCaseDict(MutableMapping[AnyStr, Any]):
    __slots__ = ('_data',)

    _data: MutableMapping[AnyStr, Any]

    def __init__(
        self, data: Optional[MutableMapping[AnyStr, Any]] = None, **kw: Any
    ) -> None:
        self._data = {}
        self.update(data or {}, **kw)

    def __setitem__(self, key: AnyStr, value: Any) -> None:
        self._data[key.lower()] = value

    def __getitem__(self, key: AnyStr) -> Any:
        return self._data[key.lower()]

    def __delitem__(self, key: AnyStr) -> None:
        del self._data[key.lower()]

    def __iter__(self) -> Iterator[Any]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({dict(self.items())})"
