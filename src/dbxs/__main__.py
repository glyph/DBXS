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


if __name__ == "__main__":
    from sys import argv

    showAllQueries(argv[1])
