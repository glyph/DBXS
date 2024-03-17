from __future__ import annotations

from asyncio import get_event_loop
from dataclasses import dataclass
from os import environ
from typing import AsyncIterable

from twisted.trial.unittest import SynchronousTestCase as TestCase

from dbxs import accessor, many, one, query

from .._typing_compat import Protocol


try:
    from mysql.connector import connect
except ImportError:
    cantFindPG = "mysql-connector-python not installed"
else:
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
                    cantFindPG = ""
    except Exception as e:
        cantFindPG = f"could not connect: {e} ({environ.get('PGPORT')})"


async def configuredConnectAsync() -> MySQLConnectionAbstract:
    return await connectAsync(
        user=environ["MYSQL_USER"], password=environ["MYSQL_PWD"]
    )


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
    if cantFindPG:
        skip = cantFindPG

    def test_basicAsyncConnection(self) -> None:
        async def _() -> None:
            self.assertIn(
                "MySQL",
                await pgia(
                    adaptMySQL(await configuredConnectAsync())
                ).getMysqlVersion(),
            )

        get_event_loop().run_until_complete(_())

    def test_valueConversions(self) -> None:
        async def _() -> None:
            everything = []
            async for row in pgia(
                adaptMySQL(await configuredConnectAsync())
            ).cannedValues("hello", 1, "second", 2):
                everything.append((row.name, row.value))
            self.assertEqual([("hello", 1), ("second", 2)], everything)

        get_event_loop().run_until_complete(_())
