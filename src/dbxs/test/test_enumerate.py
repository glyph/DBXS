"""
Tests for enumerating queries.
"""
from __future__ import annotations

from io import StringIO
from unittest import TestCase, skipIf
from unittest.mock import patch

from dbxs._enumerate import CompiledQuery, queries


try:
    __import__("sqlalchemy")
    alchemized = True
except ImportError:
    alchemized = False


class EnumerationTests(TestCase):
    def test_enumerateStrings(self) -> None:
        """
        queries() can enumerate your queries
        """
        actual = set(queries("dbxs.test.some_simple_queries", "qmark"))
        from dbxs.test.some_simple_queries import ValueAccess

        self.assertEqual(
            actual,
            {
                CompiledQuery(
                    ValueAccess,
                    "labelForID",
                    "select label from value where id = ?",
                    tuple(["id"]),
                )
            },
        )

    @skipIf(not alchemized, "SQLAlchemy not available")
    def test_enumerateStringsAlchemized(self) -> None:
        """
        queries() can enumerate your SQLAlchemy queries
        """
        actual = set(queries("dbxs.test.sqla_simple_queries", "qmark"))
        from dbxs.test.sqla_simple_queries import SQLAValueAccess

        self.assertEqual(
            actual,
            {
                CompiledQuery(
                    SQLAValueAccess,
                    "labelForIDAlchemized",
                    "\n".join(
                        [
                            "SELECT value.id, value.label ",
                            "FROM value ",
                            "WHERE value.id = ?",
                        ]
                    ),
                    tuple(["id"]),
                )
            },
        )

    @patch("sys.stdout", new_callable=StringIO)
    def test_smokeCLI(self, mockStdout: StringIO) -> None:
        """
        A quick smoke-test for the CLI, to ensure we can load all of our
        test-case and built-in queries.
        """
        from dbxs.__main__ import showAllQueries

        showAllQueries("dbxs")
        output = mockStdout.getvalue()
        self.assertIn("-- method:", output)
        self.assertIn("-- parameters: (", output)
