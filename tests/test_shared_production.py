"""Production configuration and shared SQLite behavior in isolated processes."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SharedProductionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.environment = os.environ.copy()
        self.environment.update(
            PURPLE_ENV='production',
            LAB_DATABASE=str(Path(self.directory.name) / 'shared.db'),
            SECRET_KEY='test-secret-key-' * 4,
            ALLOWED_HOSTS='example.test',
            MENTOR_PASSWORD='test-mentor-password',
            PYTHONDONTWRITEBYTECODE='1',
        )

    def run_python(self, code, environment=None):
        return subprocess.run([sys.executable, '-c', code], cwd=ROOT,
                              env=environment or self.environment,
                              text=True, capture_output=True, timeout=90)

    def test_separate_clients_share_database_and_proxy_limits_use_client_ip(self):
        result = self.run_python('''
import app
app.init_db()
first, second = app.app.test_client(), app.app.test_client()
base = 'https://example.test'
headers = {'X-Forwarded-Proto': 'https', 'X-Forwarded-For': '198.51.100.8, 192.0.2.44'}
with first.session_transaction(base_url=base) as session:
    session['csrf'] = 'one'
response = first.post('/register', base_url=base, headers=headers,
    data={'csrf_token':'one','name':'Pessoa Exemplo','email':'candidate@example.test','password':'testpass123'})
assert response.status_code == 302, response.status_code
with second.session_transaction(base_url=base) as session:
    session['csrf'] = 'two'
response = second.post('/login', base_url=base, headers=headers,
    data={'csrf_token':'two','email':'candidate@example.test','password':'testpass123'})
assert response.status_code == 302, response.status_code
assert second.get('/teams', base_url=base, headers=headers).status_code == 200
assert ('192.0.2.44', '/login') in app.RATE_BUCKETS
assert ('198.51.100.8', '/login') not in app.RATE_BUCKETS
assert second.get('/', base_url='https://invalid.test').status_code == 400
assert app.app.config['SESSION_COOKIE_SECURE']
''')
        self.assertEqual(result.returncode, 0, result.stderr)
        # The application can reopen the same persisted database after restart.
        result = self.run_python('''
import sqlite3, app
app.init_db()
with sqlite3.connect(app.DB) as connection:
    assert connection.execute("SELECT COUNT(*) FROM users WHERE email='candidate@example.test'").fetchone()[0] == 1
''')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_secret_and_unsafe_mentor_are_rejected(self):
        environment = self.environment.copy()
        environment.pop('SECRET_KEY')
        self.assertNotEqual(self.run_python('import app', environment).returncode, 0)
        environment = self.environment.copy()
        environment['MENTOR_PASSWORD'] = 'mentor123'
        result = self.run_python('import app; app.init_db()', environment)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('MENTOR_PASSWORD', result.stderr)

    def test_startup_rejects_missing_persistent_mount(self):
        environment = self.environment.copy()
        environment['PERSISTENT_MOUNT'] = self.directory.name
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/start_production.py')],
                                cwd=ROOT, env=environment, text=True, capture_output=True, timeout=30)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('mounted disk', result.stderr)


if __name__ == '__main__':
    unittest.main()
