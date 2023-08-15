from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from sqlite3 import register_adapter, register_converter
from typing import TYPE_CHECKING, AsyncIterable, Protocol
from uuid import UUID, uuid4

from twisted.internet.defer import Deferred
from twisted.internet.interfaces import IReactorCore
from twisted.python.failure import Failure

from dbxs import accessor, many, one, query, statement
from dbxs.dbapi_async import adaptSynchronousDriver, transaction


schema = """
CREATE TABLE user (
    name TEXT,
    id UUID
);
CREATE TABLE post (
    created TIMESTAMP,
    content TEXT,
    author UUID,
    id UUID,
    FOREIGN KEY(author)
        REFERENCES user(id)
        ON DELETE CASCADE
);
"""


register_adapter(UUID, lambda u: u.bytes_le)
register_converter("UUID", lambda b: UUID(bytes_le=b))


def newConnection() -> sqlite3.dbapi2.Connection:
    result = sqlite3.connect("user-posts.sqlite")
    result.create_function(
        "uuid4", 0, lambda: str(uuid4()), deterministic=False
    )
    return result


asyncDriver = adaptSynchronousDriver(
    (lambda: newConnection()), sqlite3.paramstyle
)


@dataclass
class User:
    postDB: PostDB
    id: UUID
    name: str

    async def post(self, text: str) -> None:
        return await self.postDB.makePostByUser(
            datetime.now(), text, uuid4(), self.id
        )

    def posts(self) -> AsyncIterable[Post]:
        return self.postDB.postsForUser(self.id)


@dataclass
class Post:
    postDB: PostDB
    created: datetime
    content: str
    id: UUID
    what: object


class PostDB(Protocol):
    @query(
        sql="""
        insert into user(id, name)
        values(uuid4(), {name})
        returning id, name
        """,
        load=one(User),
    )
    async def createUser(self, name: str) -> User:
        ...

    @query(
        sql="""
        select created, content, author, id
        from post
        where author = {userID}
        """,
        load=many(Post),
    )
    def postsForUser(self, userID: UUID) -> AsyncIterable[Post]:
        ...

    @statement(
        sql="""
        insert into post( created,   content,   id, author)
        values          ({created}, {content}, {id}, {author})
        """
    )
    async def makePostByUser(
        self, created: datetime, content: str, id: UUID, author: UUID
    ) -> None:
        ...


posts = accessor(PostDB)


async def main() -> None:
    async with transaction(asyncDriver) as c:
        cur = await c.cursor()
        for expr in schema.split(";"):
            await cur.execute(expr)

    async with transaction(asyncDriver) as c:
        cur = await c.cursor()
        poster = posts(c)
        b = await poster.createUser("bob")
        await b.post("a post")
        await b.post("another post")
        post: Post
        async for post in b.posts():
            print(post.created, repr(post.content))


if __name__ == "__main__":
    reactor: IReactorCore
    if not TYPE_CHECKING:
        from twisted.internet import reactor

    def reportAndStop(f: Failure | None) -> None:
        reactor.stop()
        if f is not None:
            print(f)
        else:
            return f
        print("STOP")

    reactor.callWhenRunning(
        lambda: (Deferred.fromCoroutine(main()).addBoth(reportAndStop))
    )
    reactor.run()
