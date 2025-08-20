"""
DBXS (“D.B. Access”) is an SQL database access layer for Python.
"""

from ._access import (
    ExtraneousMethods,
    IncorrectResultCount,
    NotEnoughResults,
    ParamMismatch,
    TooManyResults,
    accessor,
    many,
    maybe,
    one,
    query,
    statement,
)
from ._repository import repository


__version__ = "2025.8.20"


__all__ = [
    "one",
    "many",
    "maybe",
    "accessor",
    "repository",
    "statement",
    "query",
    "ParamMismatch",
    "TooManyResults",
    "NotEnoughResults",
    "IncorrectResultCount",
    "ExtraneousMethods",
]
