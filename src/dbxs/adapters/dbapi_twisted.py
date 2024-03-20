# -*- test-case-name: dbxs.test.test_sync_adapter -*-
"""
This adapter can convert any DB-API 2.0 driver to an L{AsyncConnectable}
asynchronous driver, using Twisted's threading infrastructure and returning
Deferreds.

While this adapter does require Twisted be installed, it does I{not}
technically require the Twisted mainloop to be running, if you supply your own
analog to L{twisted.internet.interfaces.IReactorThreads.callFromThread}.
"""

from __future__ import annotations

from dataclasses import dataclass
from queue import Queue
from threading import Thread
from typing import Any, Awaitable, Callable, Optional, Sequence, TypeVar

from twisted._threads import AlreadyQuit, ThreadWorker
from twisted._threads._ithreads import IExclusiveWorker
from twisted.internet.defer import Deferred
from twisted.python.failure import Failure

from ..async_dbapi import (
    AsyncConnectable,
    AsyncConnection,
    AsyncCursor,
    ParamStyle,
)
from ..dbapi import DBAPIColumnDescription, DBAPIConnection, DBAPICursor
from .async_pool import newPool


_T = TypeVar("_T")

F = Callable[[], None]


def _newThread() -> IExclusiveWorker:
    def _startThread(target: Callable[[], None]) -> Thread:
        thread = Thread(target=target, daemon=True)
        thread.start()
        return thread

    return ThreadWorker(_startThread, Queue())


@dataclass
class ExclusiveWorkQueue:
    _worker: Optional[IExclusiveWorker]
    _deliver: Callable[[F], None]

    def worker(self, invalidate: bool = False) -> IExclusiveWorker:
        """
        Assert that the worker should still be present, then return it
        (invalidating it if the flag is passed).
        """
        if invalidate:
            w, self._worker = self._worker, None
        else:
            w = self._worker
        if w is None:
            raise AlreadyQuit("cannot quit twice")
        return w

    def perform(
        self,
        work: Callable[[], _T],
    ) -> Deferred[_T]:
        """
        Perform the given work on the underlying thread, delivering the result
        back to the main thread with L{ExclusiveWorkQueue._deliver}.
        """

        deferred: Deferred[_T] = Deferred()

        def workInThread() -> None:
            try:
                result = work()
            except BaseException:
                f = Failure()
                self._deliver(lambda: deferred.errback(f))
            else:
                self._deliver(lambda: deferred.callback(result))

        self.worker().do(workInThread)

        return deferred

    def quit(self) -> None:
        """
        Allow this thread to stop, and invalidate this L{ExclusiveWorkQueue} by
        removing its C{_worker} attribute.
        """
        self.worker(True).quit()

    def __del__(self) -> None:
        """
        When garbage collected make sure we kill off our underlying thread.
        """
        if self._worker is None:
            return
        # might be nice to emit a ResourceWarning here, since __del__ is not a
        # good way to clean up resources.
        self.quit()


@dataclass
class ThreadedCursorAdapter(AsyncCursor):
    """
    A cursor that can be interacted with asynchronously.
    """

    _cursor: DBAPICursor
    _exclusive: ExclusiveWorkQueue

    async def description(self) -> Optional[Sequence[DBAPIColumnDescription]]:
        result: Optional[
            Sequence[DBAPIColumnDescription]
        ] = await self._exclusive.perform(lambda: self._cursor.description)
        return result

    async def rowcount(self) -> int:
        result: int = await self._exclusive.perform(
            lambda: self._cursor.rowcount
        )
        return result

    async def fetchone(self) -> Optional[Sequence[Any]]:
        result: Optional[Sequence[Any]] = await self._exclusive.perform(
            self._cursor.fetchone
        )
        return result

    # async def fetchmany(
    #     self, size: Optional[int] = None
    # ) -> Sequence[Sequence[Any]]:
    #     a = [size] if size is not None else []
    #     result: Sequence[Sequence[Any]] = await self._exclusive.perform(
    #         lambda: self._cursor.fetchmany(*a)
    #     )
    #     return result

    async def fetchall(self) -> Sequence[Sequence[Any]]:
        result: Sequence[Sequence[Any]] = await self._exclusive.perform(
            self._cursor.fetchall
        )
        return result

    async def execute(
        self,
        operation: str,
        parameters: Sequence[Any] | dict[str, Any] = (),
    ) -> object:
        """
        Execute the given statement.
        """

        def query() -> object:
            return self._cursor.execute(operation, parameters)

        return await self._exclusive.perform(query)

    # async def executemany(
    #     self, __operation: str, __seq_of_parameters: Sequence[Sequence[Any]]
    # ) -> object:
    #     def query() -> object:
    #         return self._cursor.executemany(__operation, __seq_of_parameters)

    #     return await self._exclusive.perform(query)

    async def close(self) -> None:
        """
        Close the underlying cursor.
        """
        await self._exclusive.perform(self._cursor.close)


@dataclass
class _ThreadedConnectionAdapter:
    """
    Asynchronous database connection that binds to a specific thread.
    """

    _connection: Optional[DBAPIConnection]
    _exclusive: ExclusiveWorkQueue
    _paramstyle: ParamStyle

    @property
    def paramstyle(self) -> ParamStyle:
        return self._paramstyle

    def _getConnection(self, invalidate: bool = False) -> DBAPIConnection:
        """
        Get the connection, raising an exception if it's already been
        invalidated.
        """
        c = self._connection
        assert (
            c is not None
        ), "should not be able to get a bad connection via public API"
        if invalidate:
            self._connection = None
        return c

    async def close(self) -> None:
        """
        Close the connection if it hasn't been closed yet.
        """
        connection = self._getConnection(True)
        await self._exclusive.perform(connection.close)
        self._exclusive.quit()

    async def cursor(self) -> ThreadedCursorAdapter:
        """
        Construct a new async cursor.
        """
        c = self._getConnection()
        cur = await self._exclusive.perform(c.cursor)
        return ThreadedCursorAdapter(cur, self._exclusive)

    async def rollback(self) -> None:
        """
        Roll back the current transaction.
        """
        c = self._getConnection()
        await self._exclusive.perform(c.rollback)

    async def commit(self) -> None:
        """
        Roll back the current transaction.
        """
        c = self._getConnection()
        await self._exclusive.perform(c.commit)


def _synthesizeConnector(
    createWorker: Callable[[], IExclusiveWorker],
    deliver: Callable[[Callable[[], None]], None],
    connectCallable: Callable[[], DBAPIConnection],
    paramstyle: ParamStyle,
) -> Callable[[], Awaitable[AsyncConnection]]:
    """
    Creates a callable that creates an AsyncConnection via a threadpool.
    """

    async def connector() -> _ThreadedConnectionAdapter:
        e = ExclusiveWorkQueue(createWorker(), deliver)
        connectedInThread = await e.perform(connectCallable)
        return _ThreadedConnectionAdapter(connectedInThread, e, paramstyle)

    return connector


def adaptSynchronousDriver(
    connectCallable: Callable[[], DBAPIConnection],
    paramstyle: ParamStyle,
    *,
    createWorker: Optional[Callable[[], IExclusiveWorker]] = None,
    callFromThread: Optional[Callable[[F], None]] = None,
    maxIdleConnections: int = 5,
) -> AsyncConnectable:
    """
    Adapt a synchronous DB-API 2.0 driver to be an L{AsyncConnectable} a
    Twisted thread pool.

    @note: If you do not pass your own C{callFromThread} parameter, this
        requires the Twisted reactor to be running in order to process
        responses.
    """
    if callFromThread is None:
        from twisted.internet import reactor

        callFromThread = reactor.callFromThread  # type:ignore[attr-defined]

    if createWorker is None:
        createWorker = _newThread

    return newPool(
        _synthesizeConnector(
            createWorker, callFromThread, connectCallable, paramstyle
        ),
        maxIdleConnections,
    )


__all__ = [
    "adaptSynchronousDriver",
]
