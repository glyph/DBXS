from twisted.trial.unittest import SynchronousTestCase as TestCase


try:
    from psycopg import connect
except ImportError:
    cantFindPG = "psycopg not installed"
else:
    try:
        with connect() as con:
            with con.cursor() as cur:
                cur.execute("select true")
                if cur.fetchall() == [tuple([True])]:
                    cantFindPG = ""
    except Exception as e:
        cantFindPG = f"could not connect: {e}"


class AccessTestCase(TestCase):
    if cantFindPG:
        skip = cantFindPG

    def test_connect(self) -> None:
        with connect() as con:
            with con.cursor() as cur:
                cur.execute("select true")
                self.assertEqual(cur.fetchall(), [tuple([True])])
