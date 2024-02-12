# DBXS: DataBase Acc(X)esS for python

## Quick Start

- Get it from PyPI with [`pip install dbxs`](https://pypi.org/project/dbxs/).
- Read the documentation over at
  [dbxs.readthedocs.org](https://dbxs.readthedocs.org).

## What Is It And Why Do I Want It?

DBXS is *query organizer*.  It puts your collection of SQL queries into a
traditional data-access layer, leveraging Python's built-in
[`typing.Protocol`](https://docs.python.org/3.12/library/typing.html#typing.Protocol)
provide type-safety and convenience.

DBXS aims to provide 5 properties to applications that use it:

### 1. Transparency

DBXS is plain old SQL.  Aside from interpolating placeholders based on your
chosen driver's paramstyle, it does not parse or interpret the SQL statements
that you provide it.  It does not generate SQL.  What you typed is what gets
executed.  Use whatever special features your database provides, with no layers
in the middle.

### 2. Security

It is difficult to accidentally write an SQL injection vulnerability with DBXS.
By requiring that SQL statements be written at import time, ahead of your
application code even executing, attacker-controlled data from your requests is
unlikely to be available.  If your code is using DBXS idiomatically (i.e.: not
calling out to `.execute(...)`), you can know it's safe.

### 3. Type-Safety

Although the SQL is “raw”, your results are not.  When you declare your queries
with DBXS, you describe the shape of their results in terms of dataclasses,
giving your application code structured, documented data objects to consume.
Query parameters and results are all typed.

As you're the one generating your SQL, you're still responsible for testing
that your query actually consumes and produces the types you have claimed it
does, but once you've written and tested a query.

### 4. Structure

When you use DBXS, your queries are all collected into `Protocol` classes that
define the interfaces to your data stores.  This provides a small, clear set of
locations to inspect for database query issues, both for human readers and for
metaprogramming, rather than smearing database concerns across the entirety of
your application.

Additionally, by providing a simple async context manager for transaction
management, it is far easier to scan your code for transaction boundaries by
looking for `async with transaction` than looking for calls to `commit` and
`rollback`.

### 5. Testability

The `dbxs.testing` module provides support for testing your database interfaces
with minimal set-up.  You can write a unit test that uses your database
interfaces in only a few lines of code, like so:

```python3
class MyDBXSTest(TestCase):
    @immediateTest()
    def test_myQuery(self, pool: MemoryPool) -> None:
        async with transaction(pool) as c:
            access = myAccessor(c)
            await access.createFoo("1", "hello")
            self.assertEqual((await access.getFoo("1")).name, "hello")
```

(As DBXS is still an alpha-stage project, this testing support is currently
restricted to SQLite and stdlib `unittest`, but support for arbitrary database
drivers and pytest is definitely on the roadmap.)

## Example

Using it looks like this:

```python
class Quote:
    db: QuoteDB
    id: int
    contents: str

from dbxs import query, one, many
from dbxs.dbapi_async import adaptSynchronousDriver

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

### Previous SQL Interface Solutions

When interfacing with SQL in Python, you have a few choices which predate DBXS.

You can use something low-level, specifically a [DB-API 2.0
driver](https://peps.python.org/pep-0249/), directly.  You call `connect(...)`
to get a connection, `.cursor()` on that connection to get a cursor, and
`.execute` on that cursor with some SQL and some parameters to tell the
database to do stuff.  The benefits of this approach are clear; it's very
straightforward.  If you want to do something, read the database documentation
for the SQL syntax to do the thing you want, then type in that SQL.

However, the downsides are also readily apparent, the two major ones being:

1. there are no safeguards against [SQL
   injection](https://cwe.mitre.org/data/definitions/89.html): while you *can*
   pass parameters to your SQL statements, if you *ever* have a weird edge case
   where you want to put something into a place in the query where parameters
   can't readily be used (say, if you want to let a user select a table name)
   nothing will prevent you from introducing this vulnerability.
2. every query gives you flat lists of tuples, "dumb" data which must be
   interpreted at every query site, when what you *probably* want is some kind
   of typed value object that gives it convenient methods and named attributes,
   as well as cooperating with a [type checker](https://www.mypy-lang.org).

To mitigate these disadvantages, you might use a higher-level tool like the
[Django ORM](https://docs.djangoproject.com/en/5.0/topics/db/) or
[SQLAlchemy](https://www.sqlalchemy.org).  These tools are very powerful, and
allow for many things that DBXS does not, such as dynamically composing
queries.  They provide strong affordances to make the right thing (avoiding SQL
injection) the easy thing, and they give you powerful higher-level types as
query inputs and results.

However, those introduce new problems:

1. It's a big increase in complexity.  Everyone who contributes to your project
   needs to understand *both* the SQL layer of the database *and* your ORM or
   expression layer.  While DBXS comprises a handful of functions and classes
   (mostly `query`, `one`, `many`, `statement`, `transaction`, and `accessor`,
   with `adaptSynchronousDriver` being the additional bit of glue most
   applications will need), an ORM might include dozens or even hundreds of
   additional functions and data structures.

2. This problem compounds, because if your database has any feature that you
   want to use beyond the somewhat fuzzy boundaries of “standard” SQL, even
   something as simple as `INSERT…ON CONFLICT DO NOTHING`, you need to learn
   about that feature from the [database's SQL dialect
   documentation](https://wiki.postgresql.org/wiki/UPSERT), then learn it
   *again* as you learn from the [specialized dialect
   support](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#insert-on-conflict-upsert)
   of your chosen library, assuming it wraps the feature you want.  Some
   features may only be supported as [additional libraries you need to depend
   on](https://geoalchemy-2.readthedocs.io/en/latest/) or you may have to [wait
   for them to be
   implemented](https://github.com/sqlalchemy/sqlalchemy/issues/7354).

Finally, there is a shortcoming that all these approaches have in common: they
all encourage queries to be defined on an ad-hoc basis, in the bodies of
methods and functions as the application is running.  Especially when using a
higher-level library where the SQL is generated rather than manually specified,
this can make it very difficult to go from an entry in a database log to the
location in the application code that executed it.

## Similar Systems

Does this seem familiar?  Although I hadn't heard about it at the time, I have
since learned that this is a parallel invention of [JDBI's declarative
API](https://jdbi.org/#_declarative_api).  If you notice that the ideas are
similar but the terminology is all ranodmly different, that's why.

## Limitations & Roadmap

DBXS has (as far as I know) [mostly](https://github.com/glyph/sponcom) not been
used in production, and thus should be considered alpha quality.  While its
simple implementation, small code size, and good test coverage should make
productionizing it a small amount of effort, it does still have some major
limitations compared to what I would consider a “final” release:

- DBXS only supports async database interfaces.  Many database applications
  expect a synchronous interface, and [it should have one]
  (https://github.com/glyph/DBXS/issues/18).

- DBXS only supports synchronous drivers wrapped using
  [Twisted's](https://twisted.org/) threadpool.  It should support [asyncio, as
  well as some of the native database
  drivers](https://github.com/glyph/DBXS/issues/19) for the asyncio ecosystem.
