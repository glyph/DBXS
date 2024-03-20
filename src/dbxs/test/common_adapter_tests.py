# -*- test-case-name: dbxs.test.test_pg,dbxs.test.test_mysql-*-
from __future__ import annotations

from abc import abstractmethod
from asyncio.events import get_event_loop
from unittest import TestCase

from ..async_dbapi import AsyncConnectable, transaction


class CommonMeta(type):
    """
    Metaclass to clip out the common base type so that CommonTests itself will
    not be discovered by pyunit or trial.
    """

    def __new__(
        cls, name: str, bases: tuple[type[object], ...], ns: dict[str, object]
    ) -> type[object]:
        bases = (
            ()
            if bases == tuple([TestCase])
            else tuple([CommonTests, TestCase])
        )
        return super().__new__(
            cls,
            name,
            bases,
            ns,
        )


class CommonTests(TestCase, metaclass=CommonMeta):
    @abstractmethod
    def createConnectable(self) -> AsyncConnectable:
        ...

    @abstractmethod
    def numberType(self) -> object:
        ...

    @abstractmethod
    def stringType(self) -> object:
        ...

    @abstractmethod
    def valuesSQL(self) -> str:
        ...

    def test_transaction(self) -> None:
        async def _() -> None:
            cc = self.createConnectable()
            async with transaction(cc) as t:
                cur = await t.cursor()
                await cur.execute(self.valuesSQL())
                desc = await cur.description()
                assert desc is not None
                [
                    (cname, typecode, *otherfirst),
                    (cname2, typecode2, *othersecond),
                ] = desc
                self.assertEqual(cname, "firstcol")
                self.assertEqual(cname2, "secondcol")
                self.assertEqual(self.numberType(), typecode)
                self.assertEqual(self.stringType(), typecode2)
                self.assertEqual((await cur.fetchall()), [(1, "2")])
                await cur.execute("create temporary table foo (bar int)")
                await cur.execute("insert into foo values (1)")
                self.assertEqual(await cur.rowcount(), 1)
                self.assertIsNone(await cur.description())

            with self.assertRaises(ZeroDivisionError):
                async with transaction(cc) as t:
                    cur = await t.cursor()
                    await cur.execute("insert into foo values(2)")
                    1 / 0

            async with transaction(cc) as t:
                cur = await t.cursor()
                await cur.execute("insert into foo values(3)")

            async with transaction(cc) as t:
                cur = await t.cursor()
                await cur.execute("select * from foo order by bar asc")
                rows = await cur.fetchall()
                self.assertEqual(rows, [tuple([1]), tuple([3])])

            await cc.quit()

        get_event_loop().run_until_complete(_())
