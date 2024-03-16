from twisted.trial.unittest import SynchronousTestCase as TestCase


postgresAvailable = False
try:
    from psycopg import connect
except ImportError:
    pass
else:
    try:
        with connect() as con:
            with con.cursor() as cur:
                cur.execute("select true")
                if cur.fetchall() == [tuple([True])]:
                    postgresAvailable = True
    except Exception:
        pass


class AccessTestCase(TestCase):
    skip = "postgres not available" if not postgresAvailable else None

    def test_connect(self) -> None:
        with connect() as con:
            with con.cursor() as cur:
                cur.execute("select true")
                self.assertEqual(cur.fetchall(), [tuple([True])])
