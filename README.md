# DBXS: Simple Python Database Access

Sometimes, you just want to write SQL.  No ORM, no expression language.  SQL
can be just fine.  Plain SQL exposes a lot of features from your database
engine which may not be expressible in a higher-level database abstraction.

But... you still don't want to allow for SQL injection.  And you don't want the
SQL smeared out, disorganized, in strings all over your codebase.

DBXS is a very lightweight system for organizing your queries into a
traditional data-access layer, using Python's built-in `typing.Protocol` to
ensure that your database queries are type-safe, and requiring them to be
defined at module import time, so as to avoid the possibility of accidental
string formatting on your queries based on input.

Using it looks like this:

```python
class Quote:
    db: QuoteDB
    id: int
    contents: str

from dbxs import query, one, many

class QuoteDB(Protocol):
    @query(
        sql="select id, contents from quote where id = {id}",
        load=one(Quote),
    )
    async def quoteByID(self, id: int) -> Quote:
        ...

    @query(
        sql="select id, contents from quote",
        load=many(Quote),
    )
    def allQuotes(self) -> AsyncIterable[Quote]:
        ...

quotes = accessor(QuoteDB)

driver = adaptSynchronousDriver(lambda: sqlite3.connect(...))

async def main() -> None:
    async with transaction(driver) as t:
        quotedb: QuoteDB = quotes(t)
        print("quote 1", (await quotedb.quoteByID(1)).contents)
        async for quote in quotedb.allQuotes():
            print("quote", quote.id, quote.contents)

```
