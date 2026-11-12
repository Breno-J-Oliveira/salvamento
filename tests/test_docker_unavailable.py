"""Absence of Docker is a real environment check, not a fake running container."""
import os
from contextlib import closing
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
os.environ.setdefault('SECRET_KEY', 'docker-unavailable-tests-only')
import app as module
import orchestrator


class DockerAvailabilityTests(unittest.TestCase):
    def test_missing_cli_is_explained_without_provisioning(self):
        with patch('shutil.which', return_value=None), patch.object(orchestrator, '_docker') as cli:
            result = orchestrator.availability()
            self.assertFalse(result['available'])
            self.assertEqual(result['code'], 'missing_cli')
            cli.assert_not_called()

    def test_engine_error_and_success_have_distinct_status(self):
        with patch('shutil.which', return_value='docker'), patch.object(orchestrator, '_docker', side_effect=orchestrator.DockerError('private-stderr')):
            result = orchestrator.availability()
            self.assertEqual(result['code'], 'engine_unavailable')
            self.assertNotIn('private-stderr', result['message'])
        with patch('shutil.which', return_value='docker'), patch.object(orchestrator, '_docker', return_value='test-version') as cli:
            self.assertTrue(orchestrator.availability()['available'])
            self.assertEqual(cli.call_args.args[0], 'info')

    @unittest.skipIf(shutil.which('docker'), 'Requires a host actually missing Docker; not a container success test.')
    def test_real_missing_docker_route_and_start_preserve_database(self):
        with tempfile.TemporaryDirectory() as folder:
            original = module.DB
            try:
                module.DB = os.path.join(folder, 'no-docker.db')
                module.init_db(); module.RATE_BUCKETS.clear()
                client = module.app.test_client()
                with client.session_transaction() as session:
                    session.update(user_id=1, csrf='docker-test')
                response = client.post('/admin/laboratory-status', data={'csrf_token':'docker-test'})
                self.assertEqual(response.status_code, 200)
                self.assertIn('Docker não instalado'.encode(), response.data)
                with closing(sqlite3.connect(module.DB)) as con:
                    cid = con.execute("SELECT id FROM challenges WHERE image='cti-lab/web-01'").fetchone()[0]
                response = client.post(f'/challenge/{cid}/start', data={'csrf_token':'docker-test'}, follow_redirects=True)
                self.assertEqual(response.status_code, 200)
                self.assertIn('Não foi possível iniciar o ambiente'.encode(), response.data)
                with closing(sqlite3.connect(module.DB)) as con:
                    self.assertEqual(con.execute('SELECT COUNT(*) FROM instances').fetchone()[0], 0)
                with client.session_transaction() as session:
                    session.clear()
                self.assertEqual(client.get('/admin/laboratory-status').status_code, 302)
            finally:
                module.DB = original
