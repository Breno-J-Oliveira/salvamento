"""Portable VM provisioning with synthetic assets; no hypervisor is executed."""
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import remote_labs
from scripts import prepare_local_vm as prep
from scripts import run_local_vm as supervisor


class FakeISO:
    def new(self, **kwargs):
        pass

    def add_fp(self, stream, length, **kwargs):
        pass

    def write(self, path):
        Path(path).write_bytes(b'fixture seed')

    def close(self):
        pass


class LocalVMPortabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.runtime = self.root / 'runtime-on-another-disk'
        self.runtime.mkdir()
        for name in ['qemu/qemu-img.exe', 'qemu/qemu-system-x86_64.exe', 'ubuntu-base.img', 'bridge.crt']:
            path = self.runtime / name
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(b'synthetic asset')
        self.database = self.root / 'demo.db'
        with closing(sqlite3.connect(self.database)) as con, con:
            # Fixture creation is disposable; these cases exercise lifecycle, not power-loss durability.
            con.execute('PRAGMA synchronous=OFF')
            con.execute('CREATE TABLE users(id INTEGER PRIMARY KEY)')
            remote_labs.migrate(con)
        self.pycdlib = patch.dict(sys.modules, pycdlib=SimpleNamespace(PyCdlib=FakeISO))
        self.pycdlib.start()

    def tearDown(self):
        self.pycdlib.stop()
        self.temp.cleanup()

    def rows(self):
        with closing(sqlite3.connect(self.database)) as con:
            return con.execute('SELECT id,status FROM remote_machines ORDER BY id').fetchall()

    @staticmethod
    def create_overlay(args, **kwargs):
        Path(args[-1]).write_bytes(b'fixture overlay')

    def prepared(self):
        with patch.object(prep.subprocess, 'run', side_effect=self.create_overlay):
            item = prep.prepare(self.runtime, self.database, 'Disposable fixture')
        return item, Path(item['folder']) / 'machine.json'

    def test_missing_assets_fail_before_registration(self):
        (self.runtime / 'bridge.crt').unlink()
        with self.assertRaises(ValueError):
            prep.prepare(self.runtime, self.database, 'Missing')
        self.assertEqual(self.rows(), [])
        self.assertEqual(list(self.runtime.glob('session-*')), [])

    def test_overlay_failure_does_not_register_and_preserves_folder(self):
        with patch.object(prep.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, ['fixture'])):
            with self.assertRaises(subprocess.CalledProcessError):
                prep.prepare(self.runtime, self.database, 'Failed overlay')
        self.assertEqual(self.rows(), [])
        self.assertEqual(len(list(self.runtime.glob('session-*'))), 1)

    def test_seed_failure_retires_new_machine_and_preserves_diagnostics(self):
        with patch.object(prep.subprocess, 'run', side_effect=self.create_overlay), patch.object(FakeISO, 'write', side_effect=OSError('fixture')):
            with self.assertRaises(OSError):
                prep.prepare(self.runtime, self.database, 'Failed seed')
        self.assertEqual(self.rows(), [(1, 'retired')])
        folder = next(self.runtime.glob('session-*'))
        self.assertTrue((folder / 'agent.token').exists())
        self.assertTrue((folder / 'disk.qcow2').exists())

    def test_explicit_runtime_is_used_and_machine_is_retired_on_exit(self):
        item, metadata = self.prepared()
        process = Mock(pid=123, returncode=0)
        process.poll.return_value = 0
        with patch.object(supervisor.subprocess, 'Popen', return_value=process) as launch, patch.object(supervisor.shutil, 'disk_usage', return_value=SimpleNamespace(free=4*1024**3)):
            self.assertEqual(supervisor.run(metadata, self.runtime), 0)
        args = launch.call_args.args[0]
        self.assertEqual(args[0], str(self.runtime / 'qemu/qemu-system-x86_64.exe'))
        self.assertIn('restrict=on', next(value for value in args if value.startswith('user,id=')))
        self.assertNotIn('shell', launch.call_args.kwargs)
        self.assertTrue((Path(item['folder']) / 'seed.iso').exists())
        self.assertEqual(self.rows(), [(1, 'retired')])

    def test_outside_directory_is_rejected_without_retiring_other_machine(self):
        item, metadata = self.prepared()
        item['folder'] = str(self.root)
        metadata.write_text(json.dumps(item))
        with patch.object(supervisor.subprocess, 'Popen') as launch:
            with self.assertRaises(ValueError):
                supervisor.run(metadata, self.runtime)
            launch.assert_not_called()
        self.assertEqual(self.rows(), [(1, 'available')])

    def test_retired_executor_cannot_be_reused(self):
        _, metadata = self.prepared()
        with closing(sqlite3.connect(self.database)) as con, con:
            con.execute("UPDATE remote_machines SET status='retired'")
        with patch.object(supervisor.subprocess, 'Popen') as launch:
            with self.assertRaises(ValueError):
                supervisor.run(metadata, self.runtime)
            launch.assert_not_called()

    def test_failed_process_launch_retires_the_registered_executor(self):
        _, metadata = self.prepared()
        with patch.object(supervisor.subprocess, 'Popen', side_effect=OSError('fixture')), patch.object(supervisor.shutil, 'disk_usage', return_value=SimpleNamespace(free=4*1024**3)):
            with self.assertRaises(OSError):
                supervisor.run(metadata, self.runtime)
        self.assertEqual(self.rows(), [(1, 'retired')])

    def test_existing_reservation_does_not_launch_or_retire_another_supervisor(self):
        item, metadata = self.prepared()
        lock = Path(item['folder']) / 'supervisor.lock'
        lock.write_text('existing reservation')
        with patch.object(supervisor.subprocess, 'Popen') as launch:
            with self.assertRaisesRegex(ValueError, 'reservation already exists'):
                supervisor.run(metadata, self.runtime)
            launch.assert_not_called()
        self.assertEqual(lock.read_text(), 'existing reservation')
        self.assertEqual(self.rows(), [(1, 'available')])

    def test_simultaneous_start_cannot_retire_the_first_supervisor(self):
        item, metadata = self.prepared()
        process = Mock(pid=123, returncode=0)
        process.poll.return_value = 0

        def overlapping_start(*args, **kwargs):
            with self.assertRaisesRegex(ValueError, 'reservation already exists'):
                supervisor.run(metadata, self.runtime)
            self.assertEqual(self.rows(), [(1, 'available')])
            return process

        with patch.object(supervisor.subprocess, 'Popen', side_effect=overlapping_start) as launch, patch.object(supervisor.shutil, 'disk_usage', return_value=SimpleNamespace(free=4*1024**3)):
            supervisor.run(metadata, self.runtime)
        launch.assert_called_once()
        self.assertTrue((Path(item['folder']) / 'supervisor.lock').exists())
        self.assertEqual(self.rows(), [(1, 'retired')])

    def test_low_disk_stops_before_launch_and_retires_executor(self):
        _, metadata = self.prepared()
        with patch.object(supervisor.subprocess, 'Popen') as launch, patch.object(supervisor.shutil, 'disk_usage', return_value=SimpleNamespace(free=100)):
            with self.assertRaises(ValueError):
                supervisor.run(metadata, self.runtime)
            launch.assert_not_called()
        self.assertEqual(self.rows(), [(1, 'retired')])

    def test_shutdown_timeout_uses_kill_and_still_retires_executor(self):
        _, metadata = self.prepared()
        process = Mock(pid=123, returncode=-9)
        process.poll.return_value = None
        process.wait.side_effect = [subprocess.TimeoutExpired('fixture', 15), -9]
        usage = [SimpleNamespace(free=4*1024**3), SimpleNamespace(free=100)]
        with patch.object(supervisor.subprocess, 'Popen', return_value=process), patch.object(supervisor.shutil, 'disk_usage', side_effect=usage):
            self.assertEqual(supervisor.run(metadata, self.runtime), -9)
        process.terminate.assert_called_once()
        process.kill.assert_called_once()
        self.assertEqual(self.rows(), [(1, 'retired')])

    def test_rotation_stops_on_unexpected_guest_exit(self):
        _, metadata = self.prepared()
        process = Mock(pid=123)
        process.poll.return_value = 1
        with patch.object(supervisor.subprocess, 'Popen', return_value=process) as launch, patch.object(supervisor.shutil, 'disk_usage', return_value=SimpleNamespace(free=4*1024**3)):
            with self.assertRaisesRegex(RuntimeError, 'antes do encerramento'):
                supervisor.run(metadata, self.runtime, bridge_port=8458, monitor_agent=True)
        self.assertIn('guestfwd=tcp:10.0.2.100:8443-tcp:127.0.0.1:8458', next(value for value in launch.call_args.args[0] if value.startswith('user,id=')))
        self.assertEqual(self.rows(), [(1, 'retired')])

    def test_rotation_stops_on_first_poll_timeout(self):
        _, metadata = self.prepared()
        process = Mock(pid=123)
        process.poll.return_value = None
        with patch.object(supervisor.subprocess, 'Popen', return_value=process), patch.object(supervisor.shutil, 'disk_usage', return_value=SimpleNamespace(free=4*1024**3)), patch.object(supervisor.time, 'monotonic', side_effect=[0, 901]):
            with self.assertRaisesRegex(RuntimeError, '15 minutos'):
                supervisor.run(metadata, self.runtime, monitor_agent=True)
        process.terminate.assert_called_once()
        self.assertEqual(self.rows(), [(1, 'retired')])


if __name__ == '__main__':
    unittest.main()
