import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from unittest.mock import patch

os.environ.setdefault('SECRET_KEY', 'test-only-incident-secret')
import app as module
from team_helpers import put_in_team


class IncidentIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous_db = module.DB
        module.DB = os.path.join(self.temp.name, 'incident.db')
        module.RATE_BUCKETS.clear()
        module.app.config.update(TESTING=True)
        module.init_db()
        self.client = module.app.test_client()
        with closing(sqlite3.connect(module.DB)) as con, con:
            con.execute("INSERT INTO users(name,email,password,role,team) VALUES('Teste','incident@example.test','unused','participante','QA')")
            self.uid = con.execute("SELECT id FROM users WHERE email='incident@example.test'").fetchone()[0]
            self.cid = con.execute("SELECT id FROM challenges WHERE image='cti-lab/incident-01'").fetchone()[0]
        put_in_team(module.DB, self.uid, 'Blue Team')   # o cenário de incidente é da trilha Blue Team
        with self.client.session_transaction() as session:
            session.update(user_id=self.uid, csrf='test-csrf')

    def tearDown(self):
        module.DB = self.previous_db
        self.temp.cleanup()

    def post(self, suffix, **data):
        return self.client.post(f'/challenge/{self.cid}{suffix}', data={'csrf_token':'test-csrf', **data})

    def test_seed_is_idempotent_and_no_hint_is_present(self):
        module.init_db()
        with closing(sqlite3.connect(module.DB)) as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM challenges WHERE image='cti-lab/incident-01'").fetchone()[0], 1)
        response = self.client.get(f'/challenge/{self.cid}')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Precisa de uma dica?'.encode(), response.data)

    def test_answer_requires_active_instance_and_matches_its_evidence(self):
        self.post('', flag='CTF{192.0.2.1}')
        with closing(sqlite3.connect(module.DB)) as con:
            self.assertEqual(con.execute('SELECT COUNT(*) FROM attempts WHERE challenge_id=?', (self.cid,)).fetchone()[0], 0)
        with patch.object(module.orch, 'start', return_value=12345), patch.object(module.orch, 'status', return_value=True), patch.object(module.secrets, 'token_hex', return_value='00'*8):
            self.post('/start')
            self.post('', flag='CTF{192.0.2.2}')
            self.post('', flag='CTF{192.0.2.1}')
        with closing(sqlite3.connect(module.DB)) as con:
            self.assertEqual(con.execute('SELECT correct FROM attempts WHERE challenge_id=? ORDER BY id', (self.cid,)).fetchall(), [(0,), (1,)])


if __name__ == '__main__':
    unittest.main()
