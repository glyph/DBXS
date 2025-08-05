# -*- test-case-name: dbxs.test.test_enumerate -*-
from dataclasses import dataclass
from typing import Iterable

from ._access import AccessProxy, QueryMetadata


@dataclass(frozen=True)
class CompiledQuery:
    protocolClass: type[object]
    methodName: str
    sql: str
    parameters: tuple[str, ...]


def queries(moduleName: str, dialect: str) -> Iterable[CompiledQuery]:
    from twisted.python.modules import getModule

    for module in getModule(moduleName).walkModules():
        try:
            loaded = module.load()
        except ImportError:
            continue
        for defined in loaded.__dict__.values():
            if (
                isinstance(defined, type)
                and issubclass(defined, AccessProxy)
                and defined is not AccessProxy
            ):
                protocol = defined.__dbxs_protocol__
                metadatums = QueryMetadata.filterProtocolNamespace(
                    protocol.__dict__.items()
                )
                for name, datum in metadatums:
                    sqlString, paramMap = datum.computeSQLFor(dialect)
                    yield CompiledQuery(
                        protocol, name, sqlString, tuple(paramMap.names)
                    )
