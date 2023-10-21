from datetime import datetime
from typing import AsyncIterable, Protocol


class User:
    ...


class Post:
    ...


class PostDB(Protocol):
    async def createUser(self, name: str) -> User:
        ...

    def postsForUser(self, userID: int) -> AsyncIterable[Post]:
        ...

    async def makePostByUser(
        self, created: datetime, content: str, author: int
    ) -> None:
        ...
