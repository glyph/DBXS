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


__version__ = "0.0.5"


__all__ = [
    "one",
    "many",
    "maybe",
    "accessor",
    "statement",
    "query",
    "ParamMismatch",
    "TooManyResults",
    "NotEnoughResults",
    "IncorrectResultCount",
    "ExtraneousMethods",
]
