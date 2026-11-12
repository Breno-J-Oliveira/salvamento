"""A fixture deve ser isolada, recusando sobreposição e mantendo o fluxo real."""
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'prepare_demo.py'


class DemoSetupTests(unittest.TestCase):
    def run_setup(self, destination):
        return subprocess.run([sys.executable, str(SCRIPT), str(destination)],
            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30)

    def test_fixture_is_relational_and_candidate_flow_works(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'presentation.demo.db'
            result = self.run_setup(target)
            self.assertEqual(result.returncode, 0, result.stderr)
            with closing(sqlite3.connect(target)) as connection:
                self.assertEqual(connection.execute('PRAGMA integrity_check').fetchone(), ('ok',))
                self.assertEqual(connection.execute('PRAGMA foreign_key_check').fetchall(), [])
                self.assertEqual(connection.execute('SELECT COUNT(*) FROM jobs').fetchone()[0], 2)
                self.assertEqual(set(connection.execute('SELECT status FROM applications')), {('draft',), ('interview',)})
                self.assertEqual(connection.execute('SELECT COUNT(*) FROM selection_responses').fetchone()[0], 3)
                self.assertEqual(connection.execute('SELECT COUNT(*) FROM selection_reviews').fetchone()[0], 1)
                self.assertEqual(connection.execute('SELECT COUNT(*) FROM attempts').fetchone()[0], 0)

            os.environ.setdefault('SECRET_KEY', 'test-only-demo-setup-key')
            sys.path.insert(0, str(ROOT))
            import app
            original_db = app.DB
            original_testing = app.app.config['TESTING']
            try:
                app.DB = str(target)
                app.app.config['TESTING'] = True
                client = app.app.test_client()
                with client.session_transaction() as session:
                    session['csrf'] = 'demo-csrf'
                login = client.post('/login', data=dict(csrf_token='demo-csrf',
                    email='candidato@demo.invalid', password='demonstracao123'))
                self.assertEqual(login.status_code, 302)
                applications = client.get('/my-applications')
                self.assertEqual(applications.status_code, 200)
                self.assertIn('Sua análise relacionou'.encode(), applications.data)
                self.assertNotIn(b'Nota interna sint', applications.data)
                self.assertEqual(client.get('/applications/2/form').status_code, 200)
                self.assertEqual(client.get('/my-applications/1/receipt').status_code, 200)
                self.assertEqual(client.get('/admin').status_code, 403)
            finally:
                app.DB = original_db
                app.app.config['TESTING'] = original_testing

    def test_existing_destination_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'keep.demo.db'
            target.write_bytes(b'preserve-this-file')
            result = self.run_setup(target)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(target.read_bytes(), b'preserve-this-file')

    def test_operational_database_name_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'LAB.DB'
            result = self.run_setup(target)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(target.exists())

    def test_import_does_not_create_database_or_start_server(self):
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run([sys.executable, '-c',
                'import runpy,sys; runpy.run_path(sys.argv[1],run_name="demo_import"); assert "app" not in sys.modules', str(SCRIPT)],
                cwd=folder, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(list(Path(folder).iterdir()), [])


if __name__ == '__main__':
    unittest.main()
