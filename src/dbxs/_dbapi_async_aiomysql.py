from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Mapping, Optional, Sequence, Union

from mysql.connector import paramstyle as mysqlParamStyle
from mysql.connector.aio.abstracts import (
    MySQLConnectionAbstract,
    MySQLCursorAbstract,
)

from ._dbapi_async_protocols import (
    AsyncConnection as AsyncConnectionP,
    AsyncCursor as AsyncCursorP,
    ParamStyle,
)
from .dbapi_sync import DBAPIColumnDescription


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

    async def fetchmany(
        self, size: Optional[int] = None
    ) -> Sequence[Sequence[Any]]:
        if size is not None:
            return await self._mysqlcur.fetchmany(size)
        else:
            return await self._mysqlcur.fetchmany()

    async def fetchall(self) -> Sequence[Sequence[Any]]:
        return await self._mysqlcur.fetchall()

    async def execute(
        self,
        operation: str,
        parameters: Union[Sequence[Any], Mapping[str, Any]] = (),
    ) -> object:
        if isinstance(parameters, Mapping) and not isinstance(
            parameters, dict
        ):
            parameters = dict(parameters)
        await self._mysqlcur.execute(operation, parameters)
        return None

    async def executemany(
        self, __operation: str, __seq_of_parameters: Sequence[Sequence[Any]]
    ) -> object:
        await self._mysqlcur.executemany(__operation, __seq_of_parameters)
        return None

    async def close(self) -> None:
        await self._mysqlcur.close()


@dataclass
class _MYSQL2DBXSAdapter:
    _mysqlcon: MySQLConnectionAbstract

    @property
    def paramstyle(self) -> ParamStyle:
        return mysqlParamStyle

    async def cursor(self) -> AsyncCursorP:
        return _MYSQL2DBXSCursor(await self._mysqlcon.cursor())

    async def rollback(self) -> None:
        await self._mysqlcon.rollback()

    async def commit(self) -> None:
        await self._mysqlcon.commit()

    async def close(self) -> None:
        await self._mysqlcon.close()


if TYPE_CHECKING:
    _Matchup: type[AsyncConnectionP] = _MYSQL2DBXSAdapter
