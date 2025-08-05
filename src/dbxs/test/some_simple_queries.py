# -*- test-case-name: dbxs.test.test_enumerate -*-

from __future__ import annotations

from typing import Protocol

from dbxs import accessor, one, query


class ValueAccess(Protocol):
    @query(
        sql="select label from value where id = {id}",
        load=one(lambda s: str(s)),
    )
    async def labelForID(self, id: int) -> str:
        ...


accessValue = accessor(ValueAccess)
