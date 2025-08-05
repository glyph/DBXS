# -*- test-case-name: dbxs.test.test_enumerate -*-

from typing import Protocol

from dbxs import accessor, one, query


try:
    from sqlalchemy.sql.expression import bindparam
    from sqlalchemy.sql.schema import Column, MetaData, Table
    from sqlalchemy.sql.sqltypes import Integer, String

    alchemyMetadata = MetaData()
    valueTable = Table(
        "value",
        alchemyMetadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("label", String),
    )

    alchemized = True
except ImportError:
    alchemized = False


if alchemized:

    class SQLAValueAccess(Protocol):
        @query(
            sql=(
                valueTable.select().where(valueTable.c.id == bindparam("id"))
            ),
            load=one(lambda s: str(s)),
        )
        async def labelForIDAlchemized(self, id: int) -> str:
            ...

    valueAccess = accessor(SQLAValueAccess)
