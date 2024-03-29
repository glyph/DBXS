"""
This is a collection of abstract types that are I{like} the PEP 249 types in
L{dbxs.dbapi}, but with C{await} put in the relevant places to make them
asynchronous.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Optional, Sequence, TypeVar, Union

from ._typing_compat import Protocol
from .dbapi import DBAPIColumnDescription


class InvalidConnection(Exception):
    """
    The connection has already been closed, or the transaction has already been
    committed.
    """


ParamStyle = str

# Sadly, db-api modules do not restrict themselves in this way, so we can't
# specify the ParamStyle type more precisely, like so:

# ParamStyle = Literal['qmark', 'numeric', 'named', 'format', 'pyformat']

T = TypeVar("T")


class AsyncCursor(Protocol):
    """
    Asynchronous Cursor Object.
    """

    async def description(
        self,
    ) -> Optional[Sequence[DBAPIColumnDescription]]:
        ...

    async def rowcount(self) -> int:
        ...

    async def fetchone(self) -> Optional[Sequence[Any]]:
        ...

    # async def fetchmany(
    #     self, size: Optional[int] = None
    # ) -> Sequence[Sequence[Any]]:
    #     ...

    async def fetchall(self) -> Sequence[Sequence[Any]]:
        ...

    async def execute(
        self,
        operation: str,
        parameters: Union[Sequence[Any], dict[str, Any]] = (),
    ) -> object:
        ...

    # async def executemany(
    #     self, __operation: str, __seq_of_parameters: Sequence[Sequence[Any]]
    # ) -> object:
    #     ...

    async def close(self) -> None:
        ...


class AsyncConnection(Protocol):
    """
    Asynchronous version of a DB-API connection.
    """

    @property
    def paramstyle(self) -> ParamStyle:
        ...

    async def cursor(self) -> AsyncCursor:
        ...

    async def rollback(self) -> None:
        ...

    async def commit(self) -> None:
        ...

    async def close(self) -> None:
        ...


class AsyncConnectable(Protocol):
    """
    An L{AsyncConnectable} can establish and pool L{AsyncConnection} objects.
    """

    async def connect(self) -> AsyncConnection:
        ...

    async def quit(self) -> None:
        ...


@asynccontextmanager
async def transaction(
    connectable: AsyncConnectable,
) -> AsyncIterator[AsyncConnection]:
    """
    Connect to a given connection in a context manager.
    """
    conn = await connectable.connect()
    try:
        yield conn
    except BaseException:
        await conn.rollback()
        raise
    else:
        await conn.commit()
