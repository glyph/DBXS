from dbxs._enumerate import queries


def showAllQueries(moduleName: str) -> None:
    for compiled in queries(moduleName, "named"):
        print()
        print("----")
        print(
            "-- method: "
            + compiled.protocolClass.__module__
            + "."
            + compiled.protocolClass.__qualname__
            + "."
            + compiled.methodName
        )
        print("-- parameters: " + "(" + ", ".join(compiled.parameters) + ")")
        print(compiled.sql)


if __name__ == "__main__":  # pragma: no branch
    from sys import argv  # pragma: no cover

    showAllQueries(argv[1])  # pragma: no cover
