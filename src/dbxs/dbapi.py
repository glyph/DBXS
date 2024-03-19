"""
This module is a description of the abstract types described by U{PEP 249
Database API 2.0 <https://www.python.org/dev/peps/pep-0249/>}.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence, Tuple, Union

from ._typing_compat import Protocol


DBAPITypeCode = Optional[Any]


DBAPIColumnDescription = Tuple[
    str,  # name
    DBAPITypeCode,  # type_code
    Optional[int],  # display_size
    Optional[int],  # internal_size
    Optional[int],  # precision
    Optional[int],  # scale
    Union[None, bool, int],  # null_ok
]


class DBAPIConnection(Protocol):
    def close(self) -> object:
        ...

    def commit(self) -> object:
        ...

    def rollback(self) -> Any:
        ...

    def cursor(self) -> DBAPICursor:
        ...


class DBAPICursor(Protocol):
    arraysize: int

    @property
    def description(self) -> Optional[Sequence[DBAPIColumnDescription]]:
        ...

    @property
    def rowcount(self) -> int:
        ...

    def close(self) -> object:
        ...

    def execute(
        self,
        operation: str,
        parameters: Union[Sequence[Any], Mapping[str, Any]] = ...,
    ) -> object:
        ...

    # def executemany(
    #     self, __operation: str, __seq_of_parameters: Sequence[Sequence[Any]]
    # ) -> object:
    #     ...

    def fetchone(self) -> Optional[Sequence[Any]]:
        ...

    def fetchmany(self, __size: int = ...) -> Sequence[Sequence[Any]]:
        ...

    def fetchall(self) -> Sequence[Sequence[Any]]:
        ...
