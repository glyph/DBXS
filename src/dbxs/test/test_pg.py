from __future__ import annotations

from asyncio import get_event_loop
from dataclasses import dataclass
from os import environ
from typing import AsyncIterable

from twisted.trial.unittest import SynchronousTestCase as TestCase

from dbxs import accessor, many, one, query

from .._typing_compat import Protocol


try:
    from psycopg import connect
except ImportError:
    cantFindPG = "psycopg not installed"
else:
    from psycopg import AsyncConnection

    from ..adapters._dbapi_async_psycopg3 import _PG2DBXSAdapter

    try:
        with connect() as con:
            with con.cursor() as cur:
                cur.execute("select true")
                if cur.fetchall() == [tuple([True])]:
                    cantFindPG = ""
    except Exception as e:
        cantFindPG = f"could not connect: {e} ({environ.get('PGPORT')})"


@dataclass
class SimpleRow:
    db: PGInternalsAccess
    name: str
    value: int


class PGInternalsAccess(Protocol):
    @query(sql="select version()", load=one(lambda db, x: str(x)))
    async def getPostgresVersion(self) -> str:
        ...

    @query(
        sql="""select * from
        (values ({firstName}, {firstValue}), ({secondName}, {secondValue}))
        as simple_rows(name, value)
        """,
        load=many(SimpleRow),
    )
    def cannedValues(
        self,
        firstName: str,
        firstValue: int,
        secondName: str,
        secondValue: int,
    ) -> AsyncIterable[SimpleRow]:
        ...


pgia = accessor(PGInternalsAccess)


class AccessTestCase(TestCase):
    if cantFindPG:
        skip = cantFindPG

    def test_connect(self) -> None:
        """
        Testing self-test to ensure we can still connect to the database once
        the tests are running.
        """
        with connect() as con:
            with con.cursor() as cur:
                cur.execute("select true")
                self.assertEqual(cur.fetchall(), [tuple([True])])

    def test_basicAsyncConnection(self) -> None:
        async def _() -> None:
            self.assertIn(
                "PostgreSQL",
                await pgia(
                    _PG2DBXSAdapter(await AsyncConnection.connect())
                ).getPostgresVersion(),
            )

        get_event_loop().run_until_complete(_())

    def test_valueConversions(self) -> None:
        async def _() -> None:
            everything = []
            async for row in pgia(
                _PG2DBXSAdapter(await AsyncConnection.connect())
            ).cannedValues("hello", 1, "second", 2):
                everything.append((row.name, row.value))
            self.assertEqual([("hello", 1), ("second", 2)], everything)

        get_event_loop().run_until_complete(_())
