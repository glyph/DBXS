from __future__ import annotations

from asyncio import get_event_loop
from dataclasses import dataclass
from os import environ
from typing import AsyncIterable

from twisted.trial.unittest import SynchronousTestCase as TestCase

from dbxs import accessor, many, one, query

from .._typing_compat import Protocol
from ..async_dbapi import AsyncConnectable
from .common_adapter_tests import CommonTests


try:
    from mysql.connector import connect
except ImportError:
    cantFindMySQL = "mysql-connector-python not installed"
else:
    from mysql.connector import NUMBER, STRING
    from mysql.connector.aio import connect as connectAsync
    from mysql.connector.aio.abstracts import MySQLConnectionAbstract

    from ..adapters.async_mysql import adaptMySQL

    try:
        with connect(
            user=environ["MYSQL_USER"], password=environ["MYSQL_PWD"]
        ) as con:
            with con.cursor() as cur:
                cur.execute("select true")
                if cur.fetchall() == [tuple([True])]:
                    cantFindMySQL = ""
    except Exception as e:  # pragma: nocov
        cantFindMySQL = f"could not connect: {e} ({environ.get('MYSQL_USER')})"


async def configuredConnectAsync() -> MySQLConnectionAbstract:
    connected = await connectAsync(
        user=environ["MYSQL_USER"], password=environ["MYSQL_PWD"]
    )
    cur = await connected.cursor()
    await cur.execute("create database if not exists dbxs_test_suite")
    await cur.execute("use dbxs_test_suite")
    await cur.close()
    return connected


@dataclass
class SimpleRow:
    db: MySQLInternalsAccess
    name: str
    value: int


def justStringify(
    db: MySQLInternalsAccess, varName: str, varValue: str
) -> str:
    return str(varValue)


class MySQLInternalsAccess(Protocol):
    @query(
        sql="show variables like 'version_comment'", load=one(justStringify)
    )
    async def getMysqlVersion(self) -> str:
        ...

    @query(
        sql="""select * from
        (values ROW({firstName}, {firstValue}),
         ROW({secondName}, {secondValue}))
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


pgia = accessor(MySQLInternalsAccess)


class AccessTestCase(TestCase):
    if cantFindMySQL:
        skip = cantFindMySQL

    def test_basicAsyncConnection(self) -> None:
        async def _() -> None:
            self.assertIn(
                "MySQL",
                await pgia(
                    await adaptMySQL(configuredConnectAsync).connect()
                ).getMysqlVersion(),
            )

        get_event_loop().run_until_complete(_())

    def test_valueConversions(self) -> None:
        async def _() -> None:
            everything = []
            async for row in pgia(
                await adaptMySQL(configuredConnectAsync).connect()
            ).cannedValues("hello", 1, "second", 2):
                everything.append((row.name, row.value))
            self.assertEqual([("hello", 1), ("second", 2)], everything)

        get_event_loop().run_until_complete(_())


class MySQLTests(CommonTests):
    if cantFindMySQL:
        skip = cantFindMySQL

    def createConnectable(self) -> AsyncConnectable:
        return adaptMySQL(configuredConnectAsync)

    def numberType(self) -> object:
        return NUMBER

    def stringType(self) -> object:
        return STRING

    def valuesSQL(self) -> str:
        return (
            "select * from (values row(1, '2')) as named(firstcol, secondcol)"
        )
