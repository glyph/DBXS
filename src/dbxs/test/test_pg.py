from __future__ import annotations

from asyncio import get_event_loop
from dataclasses import dataclass
from os import environ
from typing import AsyncIterable
from unittest import skipIf

from twisted.trial.unittest import SynchronousTestCase as TestCase

from dbxs import accessor, many, one, query
from dbxs.async_dbapi import transaction

from .._typing_compat import Protocol
from ..async_dbapi import AsyncConnectable
from .common_adapter_tests import CommonTests


try:
    from psycopg import connect
except ImportError:
    cantFindPG = "psycopg not installed"
else:
    from psycopg import NUMBER, STRING, AsyncConnection

    from ..adapters.async_psycopg import adaptPostgreSQL

    try:
        with connect() as con:
            with con.cursor() as cur:
                cur.execute("select true")
                if cur.fetchall() == [tuple([True])]:
                    cantFindPG = ""
    except Exception as e:  # pragma: nocov
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
                    await adaptPostgreSQL(AsyncConnection.connect).connect()
                ).getPostgresVersion(),
            )

        get_event_loop().run_until_complete(_())

    def test_valueConversions(self) -> None:
        async def _() -> None:
            everything = []
            adapted = await adaptPostgreSQL(AsyncConnection.connect).connect()
            access = pgia(adapted)
            values = access.cannedValues("hello", 1, "second", 2)
            async for row in values:
                everything.append((row.name, row.value))
            self.assertEqual([("hello", 1), ("second", 2)], everything)

        get_event_loop().run_until_complete(_())

    def test_transaction(self) -> None:
        async def _() -> None:
            async with transaction(
                adaptPostgreSQL(AsyncConnection.connect)
            ) as t:
                cur = await t.cursor()
                await cur.execute(
                    "select * from (values (1, '2')) "
                    "as named(firstcol, secondcol)"
                )
                desc = await cur.description()
                assert desc is not None
                [
                    (cname, typecode, *otherfirst),
                    (cname2, typecode2, *othersecond),
                ] = desc
                self.assertEqual(cname, "firstcol")
                self.assertEqual(cname2, "secondcol")
                self.assertEqual(NUMBER, typecode)
                self.assertEqual(STRING, typecode2)

        get_event_loop().run_until_complete(_())


@skipIf(cantFindPG, cantFindPG)
class PGTests(CommonTests):
    def createConnectable(self) -> AsyncConnectable:
        return adaptPostgreSQL(AsyncConnection.connect)

    def numberType(self) -> object:
        return NUMBER

    def stringType(self) -> object:
        return STRING

    def valuesSQL(self) -> str:
        return "select * from (values (1, '2')) as named(firstcol, secondcol)"


# print(PGTests.skip)
