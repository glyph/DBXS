"""
Tests for enumerating queries.
"""

from unittest import TestCase

from dbxs._enumerate import CompiledQuery, queries


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
