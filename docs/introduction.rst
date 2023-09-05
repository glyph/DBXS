========================
What is DBXS?
========================

DBXS is a **query organizer**.

It provides a simple structure for collecting a group of queries into a set of
methods which can be executed against a database, and to describe a way to
process the results of those queries into a data structure.

.. literalinclude:: codeexamples/userpost.py

===========
The Problem
===========

One of the biggest problems with databases today remains `SQL injection
<https://owasp.org/Top10/A03_2021-Injection/>`.




In a programming language, there are several interfaces by which one might
access a database.  Ordered from low-level to high-level, they are:

1. a *database driver*, which presents an interface that accepts strings of SQL
   and parameters, and allows you to access a database.

2. an *SQL expression model*, like `SQLAlchemy Core
   <https://docs.sqlalchemy.org/en/20/core/>`, which presents an abstract
   syntax tree, but maintains the semantics of SQL

3. an *Object Relational Mapper*, like `SQLAlchemy ORM
   <https://docs.sqlalchemy.org/en/20/orm/index.html>`.
