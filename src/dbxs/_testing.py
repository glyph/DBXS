# -*- test-case-name: dbxs.test -*-
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any, Callable, Coroutine, List, TypeVar
from unittest import TestCase
from uuid import uuid4

from twisted._threads._ithreads import IExclusiveWorker
from twisted._threads._memory import createMemoryWorker
from twisted.internet.defer import Deferred
from twisted.python.failure import Failure

from ._typing_compat import Protocol
from .adapters.dbapi_twisted import adaptSynchronousDriver
from .async_dbapi import AsyncConnectable
from .dbapi import DBAPIConnection


def sqlite3Connector() -> Callable[[], DBAPIConnection]:
    """
    Create an in-memory shared-cache SQLite3 database and return a 0-argument
    callable that will connect to that database.
    """
    uri = f"file:{str(uuid4())}?mode=memory&cache=shared"

    held = None

    def connect() -> DBAPIConnection:
        # This callable has to hang on to a connection to the underlying SQLite
        # data structures, otherwise its schema and shared cache disappear as
        # soon as it's garbage collected.  This 'nonlocal' stateemnt adds it to
        # the closure, which keeps the reference after it's created.
        nonlocal held
        return sqlite3.connect(uri, uri=True)

    held = connect()
    return connect


@dataclass
class MemoryPool:
    """
    An in-memory connection pool to an in-memory SQLite database which can be
    controlled a single operation at a time.  Each operation that would
    normally be asynchronously dispatched to a thread can be invoked with the
    L{MemoryPool.pump} and L{MemoryPool.flush} methods.

    @ivar connectable: The L{AsyncConnectable} to be passed to the system under
        test.
    """

    connectable: AsyncConnectable
    _performers: List[Callable[[], bool]]

    def additionalPump(self, f: Callable[[], bool]) -> None:
        """
        Add an additional callable to be called by L{MemoryPool.pump} and
        L{MemoryPool.flush}.  This can be used to interleave other sources of
        in-memory event completion to allow test coroutines to complete, such
        as needing to call U{StubTreq.flush
        <https://treq.readthedocs.io/en/latest/api.html#treq.testing.treq.testing.StubTreq.flush>}
        in a web application.
        """
        self._performers.append(f)

    def pump(self) -> bool:
        """
        Perform one step of pending work.

        @return: True if any work was performed and False if no work was left.
        """
        for performer in self._performers:
            if performer():
                return True
        return False

    def flush(self) -> int:
        """
        Perform all outstanding steps of work.

        @return: a count of the number of steps of work performed.
        """
        steps = 0
        while self.pump():
            steps += 1
        return steps

    @classmethod
    def new(cls) -> MemoryPool:
        """
        Create a synchronous memory connection pool.
        """
        performers = []

        def createWorker() -> IExclusiveWorker:
            worker: IExclusiveWorker
            # note: createMemoryWorker actually returns IWorker, better type
            # annotations may require additional shenanigans
            worker, perform = createMemoryWorker()
            performers.append(perform)
            return worker

        return MemoryPool(
            adaptSynchronousDriver(
                sqlite3Connector(),
                sqlite3.paramstyle,
                createWorker=createWorker,
                callFromThread=lambda f: f(),
                maxIdleConnections=10,
            ),
            performers,
        )


AnyTestCase = TypeVar("AnyTestCase", bound=TestCase)
syncAsyncTest = Callable[
    [AnyTestCase, MemoryPool],
    Coroutine[Any, Any, None],
]
regularTest = Callable[[AnyTestCase], None]


class CompletionTester(Protocol):
    def assertNoResult(self) -> None:
        """
        Raise an exception if a result is present.
        """

    def assertSuccessResult(self) -> None:
        """
        Raise an exception if a result is present.
        """


class ImmediateDriver(Protocol):
    def schedule(
        self,
        failer: Callable[[str], None],
        coroutine: Coroutine[Any, Any, Any],
    ) -> CompletionTester:
        ...


@dataclass
class DeferredCompletionTester:
    failer: Callable[[str], None]
    succeeded: list[object]
    failed: list[Failure]

    def assertNoResult(self) -> None:
        if self.failed:
            self.failed[0].raiseException()
        if self.succeeded:
            self.failer(f"unexpected result {self.succeeded[0]}")

    def assertSuccessResult(self) -> None:
        if self.failed:
            self.failed[0].raiseException()
        if not self.succeeded:
            self.failer("no result")


class ImmediateDeferred:
    @staticmethod
    def schedule(
        failer: Callable[[str], None],
        coroutine: Coroutine[Any, Any, Any],
    ) -> CompletionTester:
        succeeded: list[object] = []
        failed: list[Failure] = []
        deferred = Deferred.fromCoroutine(coroutine)
        deferred.addCallbacks(succeeded.append, failed.append)
        return DeferredCompletionTester(failer, succeeded, failed)


def immediateTest(
    driver: ImmediateDriver = ImmediateDeferred,
) -> Callable[[syncAsyncTest[AnyTestCase]], regularTest[AnyTestCase]]:
    """
    Decorate an C{async def} test that expects a coroutine.
    """

    def decorator(decorated: syncAsyncTest[AnyTestCase]) -> regularTest:
        def regular(self: AnyTestCase) -> None:
            pool = MemoryPool.new()
            d = driver.schedule(self.fail, decorated(self, pool))
            d.assertNoResult()
            while pool.flush():
                pass
            d.assertSuccessResult()

        return regular

    return decorator
