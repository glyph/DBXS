# -*- test-case-name: dbxs.test.test_pg,dbxs.test.test_mysql-*-

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
            else tuple([TestCase, CommonTests])
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
            async with transaction(self.createConnectable()) as t:
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
                self.assertEqual((await cur.fetchmany(1)), [(1, "2")])

        get_event_loop().run_until_complete(_())
