from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable

from ..async_dbapi import AsyncConnectable, AsyncConnection


@dataclass
class _GenericUnpooledConnectable:
    _connect: Callable[[], Awaitable[AsyncConnection]]

    async def connect(self) -> AsyncConnection:
        """
        Connect.
        """
        return await self._connect()

    async def quit(self) -> None:
        """
        No-op quit.
        """


def connectableFor(
    factory: Callable[[], Awaitable[AsyncConnection]]
) -> AsyncConnectable:
    return _GenericUnpooledConnectable(factory)
