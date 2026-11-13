from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest
from scripts.verify_demo import verify_demo, DEMO_MARKER


class VerifyDemoTests(unittest.TestCase):
    def test_marker_is_verified_without_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'demo.db'
            with closing(sqlite3.connect(p)) as con,con:
                con.execute('CREATE TABLE demo_metadata(name TEXT,value TEXT)')
                con.execute('INSERT INTO demo_metadata VALUES(?,?)',('fixture',DEMO_MARKER))
            before=p.read_bytes();verify_demo(p)
            self.assertEqual(p.read_bytes(),before)

    def test_missing_and_real_database_are_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'missing.db'
            with self.assertRaises(ValueError):verify_demo(p)
            self.assertFalse(p.exists())
            p=Path(folder)/'lab.db';p.write_bytes(b'preserved')
            with self.assertRaises(ValueError):verify_demo(p)
            self.assertEqual(p.read_bytes(),b'preserved')

    def test_unmarked_database_is_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'demo.db'
            with closing(sqlite3.connect(p)):pass
            with self.assertRaises(sqlite3.Error):verify_demo(p)


if __name__=='__main__':unittest.main()
