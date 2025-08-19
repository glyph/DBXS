from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, AsyncIterable, Protocol

# from userpost_sqlite import (
from userpost_gres import (
    DriverConnection,
    IntegrityError,
    driverConnect,
    driverParamStyle,
    schemaPath,
)

from twisted.internet.defer import Deferred
from twisted.internet.interfaces import IReactorCore
from twisted.python.failure import Failure

from dbxs import many, one, query, repository, statement
from dbxs.adapters.dbapi_twisted import adaptSynchronousDriver
from dbxs.async_dbapi import transaction


with schemaPath.open() as f:
    schema = f.read()


def newConnection() -> DriverConnection:
    return driverConnect()


asyncDriver = adaptSynchronousDriver(newConnection, driverParamStyle)


# user attributes
@dataclass
class User:
    postDB: PostDB
    id: int
    name: str
    # end user attributes

    async def post(self, text: str) -> None:
        return await self.postDB.makePostByUser(datetime.now(), text, self.id)

    def posts(self) -> AsyncIterable[Post]:
        return self.postDB.postsForUser(self.id)


@dataclass
class Post:
    postDB: PostDB
    created: datetime
    content: str
    id: int
    what: object


class PostDB(Protocol):
    @query(
        sql="""
        insert into "user"(name)
        values({name})
        returning id, name
        """,
        load=one(User),
    )
    async def createUser(self, name: str) -> User:
        ...

    @query(
        sql="""
        select id, name
        from "user"
        where name = {name}
        """,
        load=one(User),
    )
    async def loadUserNamed(self, name: str) -> User:
        ...

    @query(
        sql="""
        select created, content, author, id
        from post
        where author = {userID}
        """,
        load=many(Post),
    )
    def postsForUser(self, userID: int) -> AsyncIterable[Post]:
        ...

    @statement(
        sql="""
        insert into post( created,   content,   author)
        values          ({created}, {content}, {author})
        """
    )
    async def makePostByUser(
        self, created: datetime, content: str, author: int
    ) -> None:
        ...


@dataclass
class BlogRepo:
    posts: PostDB


blog = repository(BlogRepo)


async def ensureSchema() -> None:
    async with transaction(asyncDriver) as c:
        cur = await c.cursor()
        for expr in schema.split(";"):
            await cur.execute(expr)


async def makePostsBy(name: str) -> None:
    try:
        async with blog(asyncDriver) as db:
            poster = await db.posts.createUser(name)
    except IntegrityError:
        print(f"user already exists: {name}")
    async with blog(asyncDriver) as db:
        poster = await db.posts.loadUserNamed(name)
        await poster.post("a post")
        await poster.post("another post")


async def readPostsBy(name: str) -> None:
    async with blog(asyncDriver) as db:
        poster = await db.posts.loadUserNamed(name)
        async for post in poster.posts():
            print(post.created, repr(post.content))


async def main() -> None:
    await ensureSchema()
    await makePostsBy("bob")
    await readPostsBy("bob")


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
