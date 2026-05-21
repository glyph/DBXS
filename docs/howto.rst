Getting Started with DBXS
=========================

Let’s create a simple data access layer that uses DBXS to interface with its
database.  We will use the canonical example of a blog, with 2 database tables.
We will have a table of posts, and then a table of users, to attribute
authorship of those posts.

One of the primary design principles of DBXS is that, everywhere we can, we
will use *regular python features*.  We want to couple to the DBXS library in
as few places as possible.

Starting with an SQL Schema
---------------------------

DBXS is for applications that need fine-grained control over their database
interface, so let's begin by writing an SQL schema.  This is a minimal schema
for a blog with users and blog posts, with a ``FOREIGN KEY`` constraint that
relates posts to users:

.. literalinclude:: codeexamples/userpost-schema.sql
   :language: sql

This is 100% plain SQL, nothing related to DBXS at all here.

Defining your Value Classes
---------------------------

Having defined our schema in SQL, we will then want to define some simple data
structures to correspond to rows in each of the tables we have described.

For this, we will use a couple of regular ``dataclass``\es.  One for users,
which have ID numbers and names:

.. literalinclude:: codeexamples/userpost.py
   :start-after: start user attributes
   :end-before: end user attributes

and one for posts, which have an ID of their own, a user ID for their author, a
creation timestamp and their text content:

.. literalinclude:: codeexamples/userpost.py
   :start-after: start post
   :end-before: end post

The only hint that even the classes above might have *any* interface with a
database is that ``postDB`` attribute that both have, and its attendant
``PostDB`` type.  This is where we will begin using DBXS, so let's define that
type now.

Defining your Data-Access Protocol with ``typing.Protocol`` and ``@dbxs.query``
-------------------------------------------------------------------------------

The core of any DBXS data access layer is a :py:class:`typing.Protocol`, that
defines a series of methods that will interface with the database.  To begin
defining that, we will subclass :py:class:`typing.Protocol`:

.. literalinclude:: codeexamples/userpost.py
   :start-after: start postdb protocol
   :end-before: start postdb methods

The reason we are using a :py:class:`protocol <typing.Protocol>` is that we
want a type that defines all the correct method signatures and types for your
type-checker.  The concrete implementation is going to be provided by DBXS,
later.  However, although we aren't going to specify Python code to implement
these methods.  We have to tell DBXS what SQL queries these methods correspond
to.  We will do that with the ``@query`` decorator.

For our first method, let's create and return a user; taking a name, but
returning the database-generated ID.  First let's make sure we have the
relevant imports:

.. code-block:: python

   from dbxs import query, one

and then here's the method that goes in the ``PostDB`` protocol:

.. literalinclude:: codeexamples/userpost.py
   :start-after: start createUser
   :end-before: end createUser

The ``@query`` decorator requires 3 parameters:

- the method being decorated, whose parameter names, types, and return value
  we will work with
- ``sql=``, the SQL string to execute, with placeholders defined by Python's
  ``{placeholder}`` syntax.  The names in the placeholders must exactly match
  the parameters to the decorated function, and *all* parameters to the
  decorated function must be used.  Here we are doing a simple
  ``INSERT...RETURNING`` to get the database-generated user ID; note that we
  pass exactly one parameter, ``{name}``.
- ``load=``, the data-loading function we will use.  This must correspond to
  the return type.  In this case, we are using the ``one`` loader because we
  expect exactly one row to be returned, which should correspond to a ``User``.
  ``one`` will call its argument as a factory for rows returned by the query.
  First, an instance of the accessor protocol itself (in this case, ``PostDB``)
  is passed, then each column in the row.  Note that they will be passed
  positionally, so our dataclass's attributes (``postDB: PostDB``, ``id: int``,
  ``name: str``) must exactly match our expected SQL-result row shape
  (``RETURNING id, name``).

Note that this is an async method, because database access is potentially slow,
and thus should be async.  Since a query might bog down, your code needs to be
prepared to ``await`` it.

Here, we have one row, but of course, the signature of queries that return
multiple rows, or no data at all, will look different.  For examples of those,
we have ``postsForUser``:

.. literalinclude:: codeexamples/userpost.py
   :start-after: start postsForUser
   :end-before: end postsForUser

Note that this is quite similar, but in this case, the return type is now
``AsyncIterable[Post]``, and as such we have removed the ``async`` from before
the ``def``, because ``async def ...() -> AsyncIterable[...]`` would be
*double*-async, and nobody wants to ``await`` the same thing twice.

The other change is that we are now using the ``many`` loader, which is what
hooks up that ``AsyncIterable`` magic for us later:

.. code-block::

   from dbxs import many

Finally, any statement that we don't expect to have any results at all, such as
``INSERT`` *without* ``RETURNING``, should use the ``@statement`` decorator, instead.

.. code-block::

   from dbxs import statement

like so:

.. literalinclude:: codeexamples/userpost.py
   :start-after: start makePostByUser
   :end-before: end makePostByUser

Given that each of these loaders will give these row classes a ``PostDB`` to
work with itself, we can put some methods onto ``User`` as well, that call these:

.. literalinclude:: codeexamples/userpost.py
   :start-after: start user methods
   :end-before: end user methods

SQLAlchemy Core Support
-----------------------

If you are using the `SQLAlchemy Core
<https://docs.sqlalchemy.org/en/20/core/>`_ expression language, you can also
use SQLAlchemy Core expressions as your queries within your DBXS accessor
protocols instead of SQL strings.  You will need to use
:py:func:`sqlalchemy.sql.expression.bindparam` for each of your parameters,
rather than a ``{parameter}`` surrounded by curly braces in an SQL string.

For example, we can translate the ``userpost.py`` schema to SQLAlchemy Core
like so; first, we have to define the schema:

.. literalinclude:: codeexamples/userpost_alchemy.py
   :start-after: start schema definition
   :end-before: end schema definition

Then, any SQL-string-using method may be re-defined using this metadata for its
``sql=`` parameter, using ``bindparam`` as described above.  For example, here
is a working translation of the ``createUser`` method:

.. literalinclude:: codeexamples/userpost_alchemy.py
   :start-after: start createUser
   :end-before: end createUser

Note that you can mix and match raw SQL or SQLAlchemy Core expressions as much
as you’d like, even within the same protocol.

Since this is not a SQLAlchemy Core Expression Language tutorial, we will elide
the remainder of the translations, but there’s nothing new there as far as DBXS
is concerned; just write your queries as SQLAlchemy Core queries, with
``bindparam("name")`` to match your accessor method's parameter names.

.. note::

   The usage of the terminology “SQLAlchemy ***Core***” in this section is very
   intentional.  The `SQLAlchemy ORM
   <https://docs.sqlalchemy.org/en/20/orm/index.html>`_ is not supported by
   DBXS.  Due to fundamental differences in their underlying architectures, it
   is unlikely that the ORM will be supported by DBXS in the future, either.

*Why* Use SQLAlchemy Core With DBXS?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

DBXS allows you to write raw SQL to access all of your database’s features
while preventing SQL injection.  It may, therefore, seem duplicative to use
them together, when SQLAlchemy Core also already prevents SQL injection on its
own.

However, SQL injection prevention is just one feature of DBXS; its main focus
is not security; rather, its security is a side-effect of its *main* focus,
which is to *keep your queries organized*.

While there are benefits to using raw SQL (such as transparency and
simplicity), in more advanced database applications, an expression language
like SQLAlchemy Core can provide higher-level functionality that avoids a lot
of duplicate work.  For example, in raw SQL, it's very hard to write a
inequality pagination query that can operate on an arbitrary column from any
table.

When using SQLAlchemy Core without DBXS, it’s unfortunately easy to make a mess
out of your queries. They can end up smeared out all over your codebase, making
it difficult to find where a particular query is defined.  This mess can create
both legibility and efficiency challenges.

The legibility challenge is the difficulty of working backwards from a SQL
string you're looking at in database logs, trying to figure out where in the
code that particular query is defined, based on a series of functions which
incrementally build up queries as they're being executed.

The efficiency problems arise come from two separate issues.

First, because it's idiomatic to build up SQLAlchemy Core queries at runtime as
your application code is getting invoked, you can waste time re-building the
same query over and over again.  As queries grow and become more complex, the
CPU performance overhead from the sheer number of function calls needed to do
this can become significant.

Second, while Python's database API does not natively support `prepared
statements <https://en.wikipedia.org/wiki/Prepared_statement>`_, some database
drivers `use an heuristic to try to avoid
<https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#prepared-statement-cache>`_
repeatedly uploading the same SQL string to the database over and over again,
which requires that an SQL expression be *the same string* on each repeated
query to be properly cached.  According to SQLAlchemy's own documentation this
can be as much as 10% faster.  But idiomatic SQLAlchemy can easily produce
*different* statements on each execution if you're not careful, rather than
bind parameters, breaking the database driver's prepared statement heuristic
entirely.

Due to its structure, DBXS forces all SQLAlchemy Core queries to be both
defined defined and compiled to SQL once, at import time, thus inherently
preventing any duplicative construction or query variation at runtime.

Thus, if you are using SQLAlchemy Core already and you're happy with it, adding
DBXS to it will let you keep all the stuff you like while adding a layer of
structure that will make it ***both*** faster to execute and easier to debug.


Organizing Multiple Data-Access Protocols with a ``repository``
---------------------------------------------------------------

Now, you may notice that although we can put logic into our row values, we are
cramming all of the *queries* into a single class.  DBXS is a query
*organizer*, not a query pile, so in order to allow us to separate out our
queries into a *group* of related interfaces, rather than piling every query
for our entire application into a single ``class`` block, we will use a
*repository*.  A repository is just a ``dataclass`` whose attributes are each a
:py:class:`typing.Protocol` whose methods are all decorated with ``@query`` or
``@statement``.  In our case, we've only got one so far, so we can keep it
simple; a blog repository with a single attribute, the ``PostDB`` we just
defined:

.. literalinclude:: codeexamples/userpost.py
   :start-after: start repo
   :end-before: end repo

To glue all this together and make sure we have defined our ``@query`` methods correctly, we can use ``repository``:

.. code-block::

   from dbxs import repository

.. literalinclude:: codeexamples/userpost.py
   :start-after: start make repo
   :end-before: end make repo

Now, we have a ``blog`` repository that can connect up to a database for us,
but first we need to say *which* database.

Using Synchronous DB-API 2.0 Drivers with ``adaptSynchronousDriver``
--------------------------------------------------------------------

Just for starters, let's use SQLite.  In the interests of demonstrating some
cross-database functionality later on, let's put our SQLite-specific stuff in
its own file:

.. literalinclude:: codeexamples/userpost_sqlite.py

and then we will need to import it into our main program:

.. literalinclude:: codeexamples/userpost.py
   :start-after: start sqlite imports
   :end-before: end sqlite imports

Finally we can wrap this up in a way that is legible to DBXS by wrapping the
Twisted threadpool around it to adapt the standard library's synchronous driver
for SQLite into an asynchronous one:

.. code-block::

   from dbxs.adapters.dbapi_twisted import adaptSynchronousDriver

.. literalinclude:: codeexamples/userpost.py
   :start-after: start driver
   :end-before: end driver

A little bit of boilerplate to run a ``main`` function coroutine:

.. literalinclude:: codeexamples/userpost.py
   :start-after: start boilerplate
   :end-before: end boilerplate


Execuing Raw SQL using ``async with transaction(driver) as connection:``
------------------------------------------------------------------------

Now, in order to bootstrap our database and use all these fancy SQL queries
we've defined, we *will* need to somehow actually make sure our schema is
applied, and in order to do that we will make use of DBXS's transaction
abstraction as well as direct SQL execution facilities.

.. code-block::

   from dbxs.async_dbapi import transaction

Let's open up that schema file, and read it one line at a time:

.. literalinclude:: codeexamples/userpost.py
   :start-after: start ensureSchema
   :end-before: end ensureSchema

``transaction(...)`` takes our previously-declared ``asyncDriver`` and returns
an asynchronous contextmanager, i.e. an object that you can use with ``async
with`` .  The transaction begins when entering the ``with`` block, commits when
exiting it successfully and rolls back when exiting it with an error.

The ``as`` value for that block is an object like a DB-API 2 “connection”,
where all the methods are asynchronous.  So here we make a cursor, then
manually ``execute()`` each statement in our schema, splitting them by
semicolon.

Accessing your data protocols using ``async with someRepo(driver) as db:``
--------------------------------------------------------------------------

Finally, let's put it all together: let's create a user and make some posts:

.. literalinclude:: codeexamples/userpost.py
   :start-after: start makePostsBy
   :end-before: end makePostsBy

In this example you can see we are using our ``blog`` repository.  The ``db``
object that we get back as the ``as`` value here is an instance of ``BlogRepo``
(since ``blog = repository(BlogRepo)``), with each of its accessor protocol
attributes (in this case, just ``.posts``) populated with an implementation of
its type.

In other words, ``db.posts`` will be an instance of a ``PostsDB``
implementation.  As you can see, we are calling methods on it; and you already
know what types those methods return, because their type signatures all exactly
match up with the Python types we wrote above.

Just the same as ``transaction``, our ``blog`` repository callable will commit
its transaction to the underlying database when exiting the ``with`` block, or
rolling it back (as it will have to do if our attempt to create a user violates
a ``UNIQUE`` constraint and raises an ``IntegrityError``).

To demonstrate how we can consume the results of a multi-record query, let's
read some blog posts:

.. literalinclude:: codeexamples/userpost.py
   :start-after: start readPostsBy
   :end-before: end readPostsBy

Here we can consume the ``AsyncIterable`` we created before with an ``async
for``, and as described, it yields ``Post`` objects.

Review and Conclusion
---------------------

That's about it for the basic structure of DBXS.

To review the steps for using it:

1. Define your value classes in terms of basic dataclasses, or functions which
   take row outputs.
2. Connect to your database with an async driver; any synchronous driver can be
   adapted using ``adaptSynchronousDriver``.
3. Construct a data-access :py:class:`protocol <typing.Protocol>` for each
   section of your database interface, decorating all of its methods with
   ``@query`` or ``@statement``, adding ``load=`` parameters with ``one(...)`` or
   ``many(...)`` as appropriate.
4. Collect those access protocols into a repository dataclass, and make a
   factory out of it with ``repository(...)``.
5. Execute transactions against your database ``async with
   yourRep(yourDriver):``
6. Enjoy type-safe, simple data access to your SQL database!

More documentation for these other features will be forthcoming, but in the
meanwhile, if you're interested you can dive into the code and DBXS's own tests
for examples, and:

- write quick, synchronous tests for your data-access layer, using SQLite
  with ``dbxs.testing.MemoryPool`` and ``dbxs.testing.immediateTest``.
- integrate with asyncio, rather than Twisted, and native async database
  drivers for PostgreSQL and MySQL rather than a threadpool, using the packages
  in ``dbxs.adapters.*``
- use SQLAlchemy Core to generate your SQL, by passing SQLAlchemy query objects
  to the ``sql=`` rather than strings, and using
  ``sqlalchemy.sql.expression.bindparam`` rather than ``"{placeholder}"``
  syntax.
- enumerate the full text of the queries your application uses with ``python -m
  dbxs`` so you can ``EXPLAIN`` them ahead of time
