"""
Connection pooling for L{AsyncConnection}.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Awaitable, Callable, List, Optional

from ..async_dbapi import (
    AsyncConnectable,
    AsyncConnection,
    AsyncCursor,
    InvalidConnection,
)


@dataclass(eq=False)
class _PooledConnectionGuard:
    """
    Pooled connection adapter that re-adds itself back to the pool upon commit
    or rollback, and guards against direct access to the underlying connection,
    to avoid changing its state behind the back of the L{_ConnectionPool}.
    """

    _adapter: Optional[AsyncConnection]
    _pool: _ConnectionPool
    _cursors: List[AsyncCursor]

    def _original(self, invalidate: bool) -> AsyncConnection:
        """
        Check for validity, return the underlying connection, and then
        optionally invalidate this adapter.
        """
        a = self._adapter
        if a is None:
            raise InvalidConnection("The connection has already been closed.")
        if invalidate:
            self._adapter = None
        return a

    @property
    def paramstyle(self) -> str:
        return self._original(False).paramstyle

    async def cursor(self) -> AsyncCursor:
        it = await self._original(False).cursor()
        self._cursors.append(it)
        return it

    async def rollback(self) -> None:
        """
        Roll back the transaction, returning the connection to the pool.
        """
        a = self._original(True)
        try:
            await a.rollback()
        finally:
            await self._pool._checkin(self, a)

    async def _closeCursors(self) -> None:
        for cursor in self._cursors:
            await cursor.close()

    async def commit(self) -> None:
        """
        Commit the transaction, returning the connection to the pool.
        """
        await self._closeCursors()
        a = self._original(True)
        try:
            await a.commit()
        finally:
            await self._pool._checkin(self, a)

    async def close(self) -> None:
        """
        Close the underlying connection, removing it from the pool.
        """
        await self._closeCursors()
        await self._original(True).close()


@dataclass(eq=False)
class _ConnectionPool:
    """
    Database engine and connection pool.
    """

    _newConnection: Callable[[], Awaitable[AsyncConnection]]
    _idleMax: int
    _idlers: List[AsyncConnection] = field(default_factory=list)
    _active: List[_PooledConnectionGuard] = field(default_factory=list)

    async def connect(self) -> AsyncConnection:
        """
        Checkout a new connection from the pool, connecting to the database and
        opening a thread first if necessary.
        """
        txn = _PooledConnectionGuard(
            (
                self._idlers.pop()
                if self._idlers
                else await self._newConnection()
            ),
            self,
            [],
        )
        self._active.append(txn)
        return txn

    async def _checkin(
        self,
        txn: _PooledConnectionGuard,
        connection: AsyncConnection,
    ) -> None:
        """
        Check a connection back in to the pool, closing and discarding it.
        """
        self._active.remove(txn)
        if len(self._idlers) < self._idleMax:
            self._idlers.append(connection)
        else:
            await connection.close()

    async def quit(self) -> None:
        """
        Close all outstanding connections and shut down the underlying
        threadpool.
        """
        self._idleMax = 0
        while self._active:
            await self._active[0].rollback()

        while self._idlers:
            await self._idlers.pop().close()


def newPool(
    newConnection: Callable[[], Awaitable[AsyncConnection]],
    maxIdleConnections: int = 5,
) -> AsyncConnectable:
    """
    Create a new connection pool that wraps up a callable that can create an
    L{AsyncConnection}.
    """
    return _ConnectionPool(newConnection, maxIdleConnections)


__all__ = ["newPool"]
