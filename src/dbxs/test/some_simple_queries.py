from typing import Protocol

from dbxs import accessor, one, query


try:
    # from sqlalchemy.sql.expression import bindparam
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


class ValueAccess(Protocol):
    @query(
        sql="select label from value where id = {id}",
        load=one(lambda s: str(s)),
    )
    async def labelForID(self, id: int) -> str:
        ...

    # if alchemized:

    #     @query(
    #         sql=(
    #             valueTable.select().where(valueTable.c.id == bindparam("id"))
    #         ),
    #         load=one(str),
    #     )
    #     async def labelForIDAlchemized(self, bar: int) -> str:
    #         ...


accessValue = accessor(ValueAccess)
