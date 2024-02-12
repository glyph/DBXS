"""
C{DBXS} (“database access”) is an asynchronous database access layer based on
lightly organizing queries into simple data structures rather than a more
general query builder or object-relational mapping.
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
