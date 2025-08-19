# userpost.py driver interface for SQLite synchronous driver

from pathlib import Path
from sqlite3 import IntegrityError, connect, paramstyle as driverParamStyle
from sqlite3.dbapi2 import Connection as DriverConnection


schemaPath = Path(__file__).parent / "userpost-schema.sql"


def driverConnect() -> DriverConnection:
    return connect("user-posts.sqlite")


__all__ = [
    "driverParamStyle",
    "DriverConnection",
    "driverConnect",
    "IntegrityError",
    "schemaPath",
]
