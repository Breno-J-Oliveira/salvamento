"""Agent contracts and registration. Real Linux execution requires a disposable VM."""
import hashlib
from contextlib import closing
from contextlib import ExitStack
import io
import json
import os
from pathlib import Path
import platform
import sqlite3
import tempfile
import unittest
import urllib.error
from unittest.mock import patch
from types import SimpleNamespace

from scripts import lab_agent, register_lab_machine


class AgentContractTests(unittest.TestCase):
    def test_only_https_or_explicit_local_http(self):
        self.assertEqual(lab_agent.api_url('https://lab.example/'), 'https://lab.example/api/lab-agent/poll')
        self.assertTrue(lab_agent.api_url('http://127.0.0.1:5057', True).endswith('/poll'))
        for url in ('http://lab.example', 'https://user:secret@lab.example',
                    'https://lab.example/path', 'https://lab.example?key=x',
                    'file:///tmp/a', 'https://lab.example/#x'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                lab_agent.api_url(url, True)

    def test_redirects_are_refused_before_credentials_can_be_forwarded(self):
        request = lab_agent.urllib.request.Request('https://first.example')
        with self.assertRaises(urllib.error.HTTPError):
            lab_agent.NoRedirect().redirect_request(request, None, 302, 'Moved', {}, 'https://other.example')

    def test_non_linux_and_missing_isolation_are_refused(self):
        with patch.object(lab_agent.platform, 'system', return_value='Windows'):
            with self.assertRaises(ValueError):
                lab_agent.execution_identity('lab', 'C:/temp', True)
        with patch.object(lab_agent.platform, 'system', return_value='Linux'):
            with self.assertRaises(ValueError):
                lab_agent.execution_identity('lab', '/tmp', False)

    def test_executor_requires_dedicated_user_and_group(self):
        cases = [
            (999, 1001, 'lab', [], [1001]),
            (1001, 6, 'disk', [], [6]),
            (1001, 1001, 'docker', [], [1001]),
            (1001, 1001, 'lab', ['other-user'], [1001]),
            (1001, 1001, 'lab', [], [1001, 27]),
        ]
        for uid, gid, group_name, members, groups in cases:
            with self.subTest(uid=uid, gid=gid, group=group_name), ExitStack() as stack:
                stack.enter_context(patch.object(lab_agent.platform, 'system', return_value='Linux'))
                stack.enter_context(patch.object(lab_agent.os, 'geteuid', return_value=0, create=True))
                stack.enter_context(patch.object(lab_agent.os, 'getgrouplist', return_value=groups, create=True))
                stack.enter_context(patch.object(lab_agent.Path, 'is_dir', return_value=True))
                stack.enter_context(patch.object(lab_agent.Path, 'is_file', return_value=True))
                stack.enter_context(patch.object(lab_agent.subprocess, 'run',
                                                return_value=SimpleNamespace(stdout='systemd 255 (255.4)')))
                account = SimpleNamespace(pw_uid=uid, pw_gid=gid)
                primary = SimpleNamespace(gr_name=group_name, gr_mem=members)
                stack.enter_context(patch.dict('sys.modules', {
                    'pwd': SimpleNamespace(getpwnam=lambda _: account),
                    'grp': SimpleNamespace(getgrgid=lambda _: primary)}))
                with self.assertRaises(ValueError):
                    lab_agent.execution_identity('lab', str(Path.cwd()), True)

    def test_systemd_version_supports_literal_shell_arguments(self):
        for version in ('systemd 253 (253.1)', 'unknown'):
            with self.subTest(version=version), patch.object(lab_agent.subprocess, 'run',
                    return_value=SimpleNamespace(stdout=version)), self.assertRaises(ValueError):
                lab_agent.require_systemd_version()
        with patch.object(lab_agent.subprocess, 'run',
                          return_value=SimpleNamespace(stdout='systemd 255 (255.4)')) as run:
            lab_agent.require_systemd_version()
        self.assertEqual(run.call_args.args[0], ['/usr/bin/systemd-run', '--version'])
        self.assertEqual(run.call_args.kwargs['timeout'], 5)
        with patch.object(lab_agent.subprocess, 'run',
                          side_effect=lab_agent.subprocess.TimeoutExpired('version', 5)):
            with self.assertRaises(ValueError):
                lab_agent.require_systemd_version()

    def test_poll_uses_bearer_and_sends_pending_result(self):
        result = dict(command_id=1, lease_token='lease-value', output='ação ' + '\ufffd'*15900, exit_code=0)
        class Opener:
            def open(self, request, timeout):
                self.request = request
                self.timeout = timeout
                return io.BytesIO(json.dumps(dict(state='active', job=None)).encode())
        opener = Opener()
        response = lab_agent.poll(opener, 'https://lab.example/api/lab-agent/poll', 'private-token', result)
        self.assertEqual(response['state'], 'active')
        self.assertEqual(json.loads(opener.request.data)['result'], result)
        self.assertEqual(opener.request.get_header('Authorization'), 'Bearer private-token')
        self.assertEqual(opener.timeout, 15)
        self.assertLess(len(opener.request.data), 65536)

    def test_poll_rejects_unbounded_and_invalid_response(self):
        class Opener:
            def __init__(self, body):
                self.body = body
            def open(self, *args, **kwargs):
                return io.BytesIO(self.body)
        for body in (b'x' * 65537, b'{"state":"unknown"}', b'[]'):
            with self.subTest(size=len(body)), self.assertRaises(ValueError):
                lab_agent.poll(Opener(body), 'https://lab.example', 'token', None)

    def test_binary_and_unicode_output_is_safe_for_api(self):
        self.assertEqual(lab_agent.format_output(b'\x00\xff' + 'ação'.encode()), '\ufffd\ufffdação')
        output = lab_agent.format_output(b'\xff'*16000, truncated=True, expired=True)
        self.assertLessEqual(len(output), 16000)
        self.assertNotIn('\x00', output)
        self.assertIn('Saída limitada', output)
        self.assertIn('Tempo de execução', output)

    def test_secret_file_syntax_and_symlink_policy(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'machine.token'
            path.write_text('x' * 64)
            # Linux permission checks have their own tests below.
            with patch.object(lab_agent.platform, 'system', return_value='Windows'):
                self.assertEqual(lab_agent.read_token(path), 'x' * 64)
                path.write_text('short')
                with self.assertRaises(ValueError):
                    lab_agent.read_token(path)

    def test_registration_stores_hash_and_refuses_existing_secret(self):
        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / 'test.db'
            with closing(sqlite3.connect(database)):
                pass
            secret = Path(folder) / 'machine.token'
            identifier = register_lab_machine.register(database, 'VM one', secret)
            token = secret.read_text().strip()
            with closing(sqlite3.connect(database)) as con:
                row = con.execute('SELECT id,name,token_hash,status,last_seen FROM remote_machines').fetchone()
            self.assertEqual(row, (identifier, 'VM one', hashlib.sha256(token.encode()).hexdigest(), 'available', None))
            with self.assertRaises(FileExistsError):
                register_lab_machine.register(database, 'VM two', secret)
            self.assertEqual(secret.read_text().strip(), token)
            with closing(sqlite3.connect(database)) as con:
                self.assertEqual(con.execute('SELECT COUNT(*) FROM remote_machines').fetchone()[0], 1)

    def test_registration_never_creates_missing_database(self):
        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / 'missing.db'
            secret = Path(folder) / 'machine.token'
            with self.assertRaises(ValueError):
                register_lab_machine.register(database, 'VM', secret)
            self.assertFalse(database.exists())
            self.assertFalse(secret.exists())

    def test_service_enforces_identity_and_cgroup_limits(self):
        args = lab_agent.service_command('echo hello', SimpleNamespace(pw_uid=1001, pw_gid=1001),
                                         '/srv/lab', 25, 'purple-lab-test.service')
        for argument in ('--property=User=1001', '--property=Group=1001',
                         '--expand-environment=no',
                         '--property=KillMode=control-group', '--property=NoNewPrivileges=yes',
                         '--property=MemoryMax=256M', '--property=TasksMax=64',
                         '--property=RuntimeMaxSec=25', '--property=SupplementaryGroups='):
            self.assertIn(argument, args)
        self.assertEqual(args[-3:], ['/bin/sh', '-c', 'echo hello'])

    def test_stop_falls_back_to_cgroup_kill_after_timeout(self):
        with patch.object(lab_agent.subprocess, 'run', side_effect=[
                lab_agent.subprocess.TimeoutExpired('stop', 5), None]) as run:
            lab_agent.stop_service('purple-lab-test.service')
        self.assertEqual(run.call_count, 2)
        self.assertEqual(run.call_args.args[0], ['/usr/bin/systemctl', 'kill', '--signal=KILL', 'purple-lab-test.service'])

    def test_stop_nonzero_also_attempts_cgroup_kill(self):
        with patch.object(lab_agent.subprocess, 'run', side_effect=[
                SimpleNamespace(returncode=1), SimpleNamespace(returncode=0)]) as run:
            lab_agent.stop_service('purple-lab-test.service')
        self.assertEqual(run.call_count, 2)
        self.assertEqual(run.call_args.args[0], ['/usr/bin/systemctl', 'kill', '--signal=KILL', 'purple-lab-test.service'])


@unittest.skipUnless(platform.system() == 'Linux' and hasattr(os, 'geteuid') and os.geteuid() == 0
                     and Path('/run/systemd/system').is_dir(),
                     'Actual execution requires root supervisor and systemd inside a disposable Linux VM.')
class LinuxExecutionTests(unittest.TestCase):
    def test_uid_is_dropped_and_output_is_bounded(self):
        import pwd
        identity = pwd.getpwnam('nobody')
        with tempfile.TemporaryDirectory() as folder:
            os.chown(folder, identity.pw_uid, identity.pw_gid)
            result = lab_agent.execute_job(
                dict(command_id=1, lease_token='lease', command='id -u; head -c 20000 /dev/zero', timeout=5),
                lab_agent.time.time()+30, identity, folder)
            self.assertTrue(result['output'].startswith(str(identity.pw_uid)))
            self.assertLessEqual(len(result['output']), 16000)
            self.assertIn('Saída limitada', result['output'])
            self.assertNotIn('\x00', result['output'])

    def test_timeout_kills_command_group(self):
        import pwd
        identity = pwd.getpwnam('nobody')
        with tempfile.TemporaryDirectory() as folder:
            os.chown(folder, identity.pw_uid, identity.pw_gid)
            start = lab_agent.time.monotonic()
            result = lab_agent.execute_job(
                dict(command_id=1, lease_token='lease', command='sleep 20', timeout=1),
                lab_agent.time.time()+30, identity, folder)
            self.assertEqual(result['exit_code'], 124)
            self.assertLess(lab_agent.time.monotonic()-start, 5)


if __name__ == '__main__':
    unittest.main()
