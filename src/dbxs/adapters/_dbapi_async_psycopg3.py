from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Mapping, Optional, Sequence, Union

from psycopg import (
    AsyncConnection,
    AsyncCursor,
    paramstyle as psycopgParamStyle,
)

from ..async_dbapi import (
    AsyncConnection as AsyncConnectionP,
    AsyncCursor as AsyncCursorP,
    ParamStyle,
)
from ..dbapi import DBAPIColumnDescription


@dataclass
class _PG2DBXSCursor:
    _pgcur: AsyncCursor

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

    async def fetchmany(
        self, size: Optional[int] = None
    ) -> Sequence[Sequence[Any]]:
        if size is not None:
            return await self._pgcur.fetchmany(size)
        else:
            return await self._pgcur.fetchmany()

    async def fetchall(self) -> Sequence[Sequence[Any]]:
        return await self._pgcur.fetchall()

    async def execute(
        self,
        operation: str,
        parameters: Union[Sequence[Any], Mapping[str, Any]] = (),
    ) -> object:
        return await self._pgcur.execute(operation, parameters)

    async def executemany(
        self, __operation: str, __seq_of_parameters: Sequence[Sequence[Any]]
    ) -> object:
        await self._pgcur.executemany(__operation, __seq_of_parameters)
        return None

    async def close(self) -> None:
        await self._pgcur.close()


@dataclass
class _PG2DBXSAdapter:
    _pgcon: AsyncConnection

    @property
    def paramstyle(self) -> ParamStyle:
        return psycopgParamStyle

    async def cursor(self) -> AsyncCursorP:
        return _PG2DBXSCursor(self._pgcon.cursor())

    async def rollback(self) -> None:
        await self._pgcon.rollback()

    async def commit(self) -> None:
        await self._pgcon.commit()

    async def close(self) -> None:
        await self._pgcon.close()


if TYPE_CHECKING:
    _Matchup: type[AsyncConnectionP] = _PG2DBXSAdapter
