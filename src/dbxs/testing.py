"""
Testing support for L{dbxs}.

L{MemoryPool} creates a synchronous, in-memory SQLite database that can be used
for testing anything that needs an
L{dbxs.dbapi_async.AsyncConnectable}.
"""

from ._testing import MemoryPool, immediateTest


__all__ = [
    "MemoryPool",
    "immediateTest",
]
