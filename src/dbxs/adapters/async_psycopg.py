# -*- test-case-name: dbxs.test.test_pg -*-

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional, Sequence, Union

from psycopg import (
    AsyncConnection as PGAsyncConnection,
    AsyncCursor as PGAsyncCursor,
    paramstyle as psycopgParamStyle,
)

from ..async_dbapi import (
    AsyncConnectable,
    AsyncConnection,
    AsyncCursor,
    ParamStyle,
)
from ..dbapi import DBAPIColumnDescription
from .async_pool import newPool


@dataclass
class _PG2DBXSCursor:
    _pgcur: PGAsyncCursor

    async def description(
        self,
    ) -> Optional[Sequence[DBAPIColumnDescription]]:
        subdesc = self._pgcur.description
        if subdesc is None:
            return None
        return [tuple(each) for each in subdesc]

    async def rowcount(self) -> int:
        return self._pgcur.rowcount

    async def fetchone(self) -> Optional[Sequence[Any]]:
        return await self._pgcur.fetchone()

    # async def fetchmany(
    #     self, size: Optional[int] = None
    # ) -> Sequence[Sequence[Any]]:
    #     if size is not None:
    #         return await self._pgcur.fetchmany(size)
    #     else:
    #         return await self._pgcur.fetchmany()

    async def fetchall(self) -> Sequence[Sequence[Any]]:
        return await self._pgcur.fetchall()

    async def execute(
        self,
        operation: str,
        parameters: Union[Sequence[Any], dict[str, Any]] = (),
    ) -> object:
        return await self._pgcur.execute(operation, parameters)

    # async def executemany(
    #     self, __operation: str, __seq_of_parameters: Sequence[Sequence[Any]]
    # ) -> object:
    #     await self._pgcur.executemany(__operation, __seq_of_parameters)
    #     return None

    async def close(self) -> None:
        await self._pgcur.close()


@dataclass
class _PG2DBXSAdapter:
    _pgcon: PGAsyncConnection

    @property
    def paramstyle(self) -> ParamStyle:
        return psycopgParamStyle

    async def cursor(self) -> AsyncCursor:
        return _PG2DBXSCursor(self._pgcon.cursor())

    async def rollback(self) -> None:
        await self._pgcon.rollback()

    async def commit(self) -> None:
        await self._pgcon.commit()

    async def close(self) -> None:
        await self._pgcon.close()


def adaptPostgreSQL(
    connect: Callable[[], Awaitable[PGAsyncConnection]]
) -> AsyncConnectable:
    """
    Adapt a connection created by U{psycopg.AsyncConnection.connect
    <https://www.psycopg.org/psycopg3/docs/api/connections.html#psycopg.AsyncConnection.connect>}
    to an L{AsyncConnection}.
    """

    async def convert() -> AsyncConnection:
        return _PG2DBXSAdapter(await connect())

    return newPool(convert)


__all__ = [
    "adaptPostgreSQL",
]
