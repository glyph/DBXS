Getting Started with DBXS
=================

Let’s create a simple data access layer that uses DBXS to interface with its
database.  We will use the canonical example of a blog, with 2 database tables.
We will have a table of posts, and then a table of users, to attribute
authorship of those posts.

One of the primary design principles of DBXS is that, everywhere we can, we
will use *regular python features*.  We want to couple to the DBXS library in
as few places as possible.

Therefore, to begin with, we will use a couple of regular ``dataclass``\es.  One
for users, which have ID numbers and names:

.. literalinclude:: codeexamples/userpost.py
   :start-after: start user attributes
   :end-before: end user attributes

and one for posts, which have an ID of their own, a user ID for their author, a
creation timestamp and their text content:

.. literalinclude:: codeexamples/userpost.py
   :start-after: start post
   :end-before: end post

DBXS is for applications that need fine-grained control over their database
interface, so let's just write a SQL schema that corresponds to these data
types by hand, with columns that correspond to the attributes, complete with a
``FOREIGN KEY`` constraint that relates posts to users:

.. literalinclude:: codeexamples/userpost-schema.sql

This is 100% plain SQL, nothing related to DBXS at all here.

The only hint that even the classes above might have *any* interface with a
database is that ``postDB`` attribute that both have, and its attendant
``PostDB`` type.  So let's define that now.

The core of any DBXS data access layer is a :py:class:`typing.Protocol`, that
defines a series of methods that will interface with the database, so let's
start defining that.

.. literalinclude:: codeexamples/userpost.py
   :start-after: start postdb protocol
   :end-before: start postdb methods

The reason we are using an abstract protocol is that we want a type that
defines all the correct method signatures and types for your type-checker, but
the concrete implementation is going to be provided by DBXS, later.  However,
although we aren't going to specify Python code to implement these methods, we
have to tell DBXS what SQL queries these methods correspond to.  We will do
that with the ``@query`` decorator.  For our first method, let's create and
return a user; taking a name, but returning the database-generated ID.  First
let's make sure we have the relevant imports:

.. code-block::
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
but first we need to say *which* database.  Just for starters, let's use
SQLite.  In the interests of demonstrating some cross-database functionality
later on, let's put our SQLite-specific stuff in its own file:

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

Here we simply consume the ``AsyncIterable`` we created before with an ``async
for``, and as described, it is a series of ``Post`` objects.
