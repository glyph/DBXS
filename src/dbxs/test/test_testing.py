from unittest import TestCase

from twisted.internet.defer import Deferred

from dbxs.testing import MemoryPool, immediateTest


class TestFailing(TestCase):
    """
    Tests for assertion methods which are normally not invoked in in a
    successful test run.
    """

    def test_immediateFailsToBlock(self) -> None:
        """
        If an @immediateTest fails to block, it fails.
        """

        @immediateTest()
        async def method(self: TestFailing, pool: MemoryPool) -> None:
            ...

        with self.assertRaises(AssertionError):
            method(self)

    def test_immediateBlocksForever(self) -> None:
        """
        If an @immediateTest blocks on something that does not immediately
        return when the memory pool is flushed, it fails.
        """

        @immediateTest()
        async def method(self: TestFailing, pool: MemoryPool) -> None:
            await Deferred()

        with self.assertRaises(AssertionError):
            method(self)

    def test_failsBeforeBlocking(self) -> None:
        """
        If an @immediateTest raises an exception, that exception is re-raised.
        """

        @immediateTest()
        async def method(self: TestFailing, pool: MemoryPool) -> None:
            1 / 0

        with self.assertRaises(ZeroDivisionError):
            method(self)

    def test_failsAfterBlocking(self) -> None:
        """
        If an @immediateTest raises an exception after blocking, that exception
        is re-raised as well.
        """

        @immediateTest()
        async def method(self: TestFailing, pool: MemoryPool) -> None:
            await pool.connectable.connect()
            1 / 0

        with self.assertRaises(ZeroDivisionError):
            method(self)
