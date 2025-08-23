from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import AsyncIterable, Protocol

from dbxs import many, one, query, repository, statement
from dbxs.adapters.dbapi_twisted import adaptSynchronousDriver
from dbxs.async_dbapi import transaction


POSTGRES = False

IntegrityError: type[Exception]
if POSTGRES:
    from userpost_gres import (
        IntegrityError,
        driverConnect,
        driverParamStyle,
        schemaPath,
    )
else:
    # start sqlite imports
    from userpost_sqlite import (
        IntegrityError,
        driverConnect,
        driverParamStyle,
        schemaPath,
    )

    # end sqlite imports


with schemaPath.open() as f:
    schema = f.read()


# start driver
asyncDriver = adaptSynchronousDriver(driverConnect, driverParamStyle)
# end driver


# start user attributes
@dataclass
class User:
    postDB: PostDB
    id: int
    name: str
    # end user attributes

    # start user methods
    async def post(self, text: str) -> None:
        return await self.postDB.makePostByUser(datetime.now(), text, self.id)

    def posts(self) -> AsyncIterable[Post]:
        return self.postDB.postsForUser(self.id)
        # end user methods


# start post
@dataclass
class Post:
    postDB: PostDB
    postID: int
    authorID: int
    created: datetime
    content: str
    # end post


# start postdb protocol
class PostDB(Protocol):
    # start postdb methods
    # start createUser
    @query(
        sql="""
        INSERT INTO "user"(name)
        VALUES({name})
        RETURNING id, name
        """,
        load=one(User),
    )
    async def createUser(self, name: str) -> User:
        ...
        # end createUser

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

    # start postsForUser
    @query(
        sql="""
        select id, author, created, content
        from post
        where author = {userID}
        """,
        load=many(Post),
    )
    def postsForUser(self, userID: int) -> AsyncIterable[Post]:
        ...
        # end postsForUser

    # start makePostByUser
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
        # end makePostByUser


# start repo
@dataclass
class BlogRepo:
    posts: PostDB
    # end repo


# start make repo
blog = repository(BlogRepo)
# end make repo


# start ensureSchema
async def ensureSchema() -> None:
    async with transaction(asyncDriver) as c:
        cur = await c.cursor()
        for expr in schema.split(";"):
            await cur.execute(expr)
    # end ensureSchema


# start makePostsBy
async def makePostsBy(name: str) -> None:
    try:
        async with blog(asyncDriver) as db:
            poster = await db.posts.createUser(name)
            print(f"created poster: {poster.name}")
    except IntegrityError:
        print(f"user already exists: {name}")
    async with blog(asyncDriver) as db:
        poster = await db.posts.loadUserNamed(name)
        await poster.post("a post")
        await poster.post("another post")
    # end makePostsBy


# start readPostsBy
async def readPostsBy(name: str) -> None:
    async with blog(asyncDriver) as db:
        poster = await db.posts.loadUserNamed(name)
        async for post in poster.posts():
            print(post.created, repr(post.content))
    # end readPostsBy


# start main
async def main(reactor: object) -> None:
    await ensureSchema()
    await makePostsBy("bob")
    await readPostsBy("bob")
    # end main


# start boilerplate
if __name__ == "__main__":
    from twisted.internet.task import react

    react(main)
# end boilerplate
