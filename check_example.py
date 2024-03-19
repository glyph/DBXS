from __future__ import annotations

from dataclasses import dataclass
from sqlite3 import connect, paramstyle
from typing import AsyncIterable, Protocol


@dataclass
class Quote:
    db: QuoteDB
    id: int
    contents: str


from dbxs import accessor, many, one, query, statement
from dbxs.adapters.dbapi_twisted import adaptSynchronousDriver
from dbxs.async_dbapi import transaction
from dbxs.dbapi import DBAPIConnection


class QuoteDB(Protocol):
    @query(sql="SELECT id, contents FROM quote WHERE id={id}", load=one(Quote))
    async def quoteByID(self, id: int) -> Quote:
        ...

    @query(sql="SELECT id, contents FROM quote", load=many(Quote))
    def allQuotes(self) -> AsyncIterable[Quote]:
        ...

    @statement(sql="INSERT INTO quote (contents) VALUES ({text})")
    async def addQuote(self, text: str) -> None:
        ...


def sqliteWithSchema() -> DBAPIConnection:
    c = connect(":memory:")
    c.execute(
        "CREATE TABLE quote (contents, id INTEGER PRIMARY KEY AUTOINCREMENT)"
    )
    c.commit()
    return c


driver = adaptSynchronousDriver(sqliteWithSchema, paramstyle)
quotes = accessor(QuoteDB)


async def main() -> None:
    async with transaction(driver) as t:
        quotedb: QuoteDB = quotes(t)
        await quotedb.addQuote("hello, world")
        async for quote in quotedb.allQuotes():
            matched = (await quotedb.quoteByID(quote.id)) == quote
            print(f"quote ({quote.id}) {quote.contents!r} {matched}")


if __name__ == "__main__":
    from twisted.internet.defer import Deferred
    from twisted.internet.task import react

    @react
    def run(reactor: object) -> Deferred[None]:
        return Deferred.fromCoroutine(main())
