from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import patch

from scripts import rotate_local_vm as rotation


class VMRotationTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.runtime = Path(folder.name)
        self.database = self.runtime / 'demo.db'
        with closing(sqlite3.connect(self.database)) as con:
            con.execute('CREATE TABLE remote_machines(status TEXT, last_seen INTEGER)')

    def insert_machine(self, seen):
        with closing(sqlite3.connect(self.database)) as con, con:
            con.execute("INSERT INTO remote_machines VALUES('available',?)", (seen,))

    def test_duplicate_operator_cannot_prepare_and_lock_releases(self):
        with rotation.operator_lock(self.database):
            with self.assertRaisesRegex(RuntimeError, 'Outra rotação'):
                with rotation.operator_lock(self.database):
                    self.fail('A second operator acquired the same lock')
        with rotation.operator_lock(self.database):
            pass

    def test_existing_machine_is_preserved_until_it_retires(self):
        self.insert_machine(int(time.time()))
        def retire(_):
            with closing(sqlite3.connect(self.database)) as con, con:
                con.execute("UPDATE remote_machines SET status='retired'")
        with patch.object(rotation.time, 'sleep', side_effect=retire) as wait:
            rotation.wait_for_existing(self.database)
        wait.assert_called_once()

    def test_disconnected_machine_blocks_new_allocation(self):
        self.insert_machine(int(time.time()) - 200)
        with self.assertRaisesRegex(RuntimeError, 'sem contato'):
            rotation.wait_for_existing(self.database)

    def test_existing_machine_without_first_poll_has_a_boot_deadline(self):
        self.insert_machine(None)
        with patch.object(rotation.time, 'monotonic', side_effect=[0, 901]):
            with self.assertRaisesRegex(RuntimeError, 'primeiro contato'):
                rotation.wait_for_existing(self.database)

    def test_stops_on_bridge_failure_without_creating_a_machine(self):
        with patch.object(rotation, 'check_bridge', side_effect=OSError), patch.object(rotation, 'prepare') as prepare:
            with self.assertRaises(OSError):
                rotation.rotate(self.runtime, self.database, 8458, 2)
            prepare.assert_not_called()

    def test_guest_failure_stops_the_batch(self):
        machine = dict(machine_id=1, folder=str(self.runtime))
        with patch.object(rotation, 'check_bridge'), patch.object(rotation, 'prepare', return_value=machine) as prepare, \
                patch.object(rotation, 'run', side_effect=RuntimeError('VM offline')):
            with self.assertRaisesRegex(RuntimeError, 'offline'):
                rotation.rotate(self.runtime, self.database, 8458, 2)
            prepare.assert_called_once()

    def test_count_requires_finite_batch(self):
        for count in (0, 51):
            with self.subTest(count=count), self.assertRaises(ValueError):
                rotation.rotate(self.runtime, self.database, 8443, count)
