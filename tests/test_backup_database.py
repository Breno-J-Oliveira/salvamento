import importlib.util
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('backup_database', Path(__file__).resolve().parents[1] / 'scripts' / 'backup_database.py')
backup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup)


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.source = Path(self.directory.name) / 'source.db'
        self.destination = Path(self.directory.name) / 'backup.db'
        with closing(sqlite3.connect(self.source)) as connection, connection:
            connection.execute('CREATE TABLE evidence(value TEXT)')
            connection.execute('INSERT INTO evidence VALUES(?)', ('synthetic-evidence',))

    def tearDown(self):
        self.directory.cleanup()

    def test_backup_and_restore_into_new_files_preserve_data(self):
        before = self.source.read_bytes()
        backup.copy_verified(self.source, self.destination)
        restored = self.destination.with_name('restored.db')
        backup.copy_verified(self.destination, restored)
        self.assertEqual(before, self.source.read_bytes())
        with closing(sqlite3.connect(restored)) as connection:
            self.assertEqual(connection.execute('SELECT value FROM evidence').fetchall(), [('synthetic-evidence',)])
            self.assertEqual(connection.execute('PRAGMA integrity_check').fetchone(), ('ok',))

    def test_existing_destination_and_same_source_are_never_overwritten(self):
        self.destination.write_bytes(b'preserve-existing-file')
        with self.assertRaises(FileExistsError):
            backup.copy_verified(self.source, self.destination)
        self.assertEqual(self.destination.read_bytes(), b'preserve-existing-file')
        with self.assertRaises(ValueError):
            backup.copy_verified(self.source, self.source)

    def test_invalid_source_does_not_leave_partial_copy(self):
        self.source.write_bytes(b'not a sqlite database')
        with self.assertRaises(sqlite3.DatabaseError):
            backup.copy_verified(self.source, self.destination)
        self.assertFalse(self.destination.exists())

    def test_missing_source_does_not_create_destination(self):
        with self.assertRaises(FileNotFoundError):
            backup.copy_verified(self.source.with_name('missing.db'), self.destination)
        self.assertFalse(self.destination.exists())

    def test_wal_snapshot_includes_committed_uncheckpointed_changes(self):
        with closing(sqlite3.connect(self.source)) as connection:
            connection.execute('PRAGMA journal_mode=WAL')
            connection.execute('INSERT INTO evidence VALUES(?)', ('committed-in-wal',))
            connection.commit()
            backup.copy_verified(self.source, self.destination)
        with closing(sqlite3.connect(self.destination)) as connection:
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM evidence').fetchone()[0], 2)
