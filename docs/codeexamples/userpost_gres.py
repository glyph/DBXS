# userpost.py driver interface for PostgreSQL synchronous driver

from pathlib import Path
from typing import Callable

from psycopg import connect, paramstyle as driverParamStyle

from dbxs.dbapi import DBAPIConnection


# psycopg's type specification for its column description is a subtype of
# Sequence[Any], which cannot match our more precise spec-compliant tuple of
# fields.  At runtime, psycopg is careful to present a sequence-ish interface
# that does return the relevant fields in an indexable way that can be accessed
# or unpacked, but it doesn't look like that to mypy, so we lie here.
driverConnect: Callable[[], DBAPIConnection]
driverConnect = connect  # type:ignore[assignment]

# Similarly, we need our DriverConnection type to match up.
DriverConnection = DBAPIConnection

from psycopg import IntegrityError


schemaPath = Path(__file__).parent / "userpost-gres.sql"
__all__ = [
    "driverParamStyle",
    "DriverConnection",
    "driverConnect",
    "IntegrityError",
    "schemaPath",
]
