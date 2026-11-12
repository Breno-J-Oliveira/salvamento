"""Regression checks for local browser boundaries and persistent attempt limits."""
import os
import sqlite3
import tempfile
import time
import unittest
from contextlib import closing

os.environ.setdefault('SECRET_KEY', 'test-security-only')
import app as module


class SecurityFinalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous_db = module.DB
        module.DB = os.path.join(self.temp.name, 'security.db')
        module.app.config['TESTING'] = True
        module.RATE_BUCKETS.clear()
        module.init_db()
        self.client = module.app.test_client()

    def tearDown(self):
        module.DB = self.previous_db
        self.temp.cleanup()

    def test_untrusted_host_rejected_and_local_hosts_allowed(self):
        self.assertEqual(self.client.get('/login', base_url='http://attacker.example').status_code, 400)
        for host in ('http://localhost', 'http://127.0.0.1:5000'):
            self.assertEqual(self.client.get('/login', base_url=host).status_code, 200)

    def test_cross_origin_post_rejected_even_with_valid_csrf(self):
        with self.client.session_transaction() as session:
            session['csrf'] = 'valid-test-token'
        data = {'csrf_token':'valid-test-token', 'email':'unknown@example.test', 'password':'invalid'}
        self.assertEqual(self.client.post('/login', data=data, headers={'Origin':'https://attacker.example'}).status_code, 403)
        self.assertEqual(self.client.post('/login', data=data, headers={'Sec-Fetch-Site':'cross-site'}).status_code, 403)
        self.assertEqual(self.client.post('/login', data=data, headers={'Origin':'http://localhost'}).status_code, 200)

    def test_browser_security_headers(self):
        response = self.client.get('/login')
        policy = response.headers['Content-Security-Policy']
        for directive in ("script-src 'self'", "object-src 'none'", "base-uri 'none'", "frame-ancestors 'none'", "form-action 'self'"):
            self.assertIn(directive, policy)
        self.assertIn('camera=()', response.headers['Permissions-Policy'])

    def test_incident_limit_is_persistent_across_session_and_instance_restart(self):
        now = int(time.time())
        with closing(sqlite3.connect(module.DB)) as connection, connection:
            connection.execute("INSERT INTO users(name,email,password,role) VALUES('QA','security@example.test','unused','participante')")
            uid = connection.execute("SELECT id FROM users WHERE email='security@example.test'").fetchone()[0]
            cid = connection.execute("SELECT id FROM challenges WHERE image='cti-lab/incident-01'").fetchone()[0]
            connection.executemany('INSERT INTO attempts(user_id,challenge_id,correct,created_at) VALUES(?,?,0,?)', [(uid,cid,now)]*12)
            connection.execute('INSERT INTO instances(user_id,challenge_id,container,port,flag_hash,started_at,expires_at,active) VALUES(?,?,?,?,?,?,?,1)',
                               (uid,cid,'lab-u2-c13-abcdef',12345,module.h('CTF{192.0.2.2}'),now,now+3600))
        module.RATE_BUCKETS.clear()
        with self.client.session_transaction() as session:
            session.update(user_id=uid, csrf='valid-test-token')
        response = self.client.post(f'/challenge/{cid}', data={'csrf_token':'valid-test-token', 'flag':'CTF{192.0.2.2}'})
        self.assertEqual(response.status_code, 429)
        with closing(sqlite3.connect(module.DB)) as connection:
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM attempts WHERE user_id=?', (uid,)).fetchone()[0], 12)
