# -*- test-case-name: dbxs.test.test_mysql -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional, Sequence, Union

from mysql.connector import paramstyle as mysqlParamStyle
from mysql.connector.aio.abstracts import (
    MySQLConnectionAbstract,
    MySQLCursorAbstract,
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
class _MYSQL2DBXSCursor:
    _mysqlcur: MySQLCursorAbstract

    async def description(
        self,
    ) -> Optional[Sequence[DBAPIColumnDescription]]:
        real = self._mysqlcur.description
        if real is None:
            return None
        return [desc[:7] for desc in real]

    async def rowcount(self) -> int:
        return self._mysqlcur.rowcount

    async def fetchone(self) -> Optional[Sequence[Any]]:
        return await self._mysqlcur.fetchone()

    # async def fetchmany(
    #     self, size: Optional[int] = None
    # ) -> Sequence[Sequence[Any]]:
    #     if size is not None:
    #         return await self._mysqlcur.fetchmany(size)
    #     else:
    #         return await self._mysqlcur.fetchmany()

    async def fetchall(self) -> Sequence[Sequence[Any]]:
        return await self._mysqlcur.fetchall()

    async def execute(
        self,
        operation: str,
        parameters: Union[Sequence[Any], dict[str, Any]] = (),
    ) -> object:
        await self._mysqlcur.execute(operation, parameters)
        return None

    # async def executemany(
    #     self, __operation: str, __seq_of_parameters: Sequence[Sequence[Any]]
    # ) -> object:
    #     await self._mysqlcur.executemany(__operation, __seq_of_parameters)
    #     return None

    async def close(self) -> None:
        await self._mysqlcur.close()


@dataclass
class _MYSQL2DBXSAdapter:
    _mysqlcon: MySQLConnectionAbstract

    @property
    def paramstyle(self) -> ParamStyle:
        return mysqlParamStyle

    async def cursor(self) -> AsyncCursor:
        return _MYSQL2DBXSCursor(await self._mysqlcon.cursor())

    async def rollback(self) -> None:
        await self._mysqlcon.rollback()

    async def commit(self) -> None:
        await self._mysqlcon.commit()

    async def close(self) -> None:
        await self._mysqlcon.close()


def adaptMySQL(
    connection: Callable[[], Awaitable[MySQLConnectionAbstract]]
) -> AsyncConnectable:
    """
    Adapt a connection created by U{mysql.connector.aio.connect
    <https://dev.mysql.com/doc/connector-python/en/connector-python-asyncio.html>}
    to an L{AsyncConnection}.
    """

    async def convert() -> AsyncConnection:
        return _MYSQL2DBXSAdapter(await connection())

    return newPool(convert)


__all__ = [
    "adaptMySQL",
]
