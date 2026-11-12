"""Remote worker protocol and private observer flow, isolated from real workers."""
import hashlib
import os
import sqlite3
import tempfile
import time
import unittest
import uuid
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor

os.environ.setdefault('SECRET_KEY', 'remote-tests-only')
import app as module
import remote_labs


class RemoteLabsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_db = module.DB
        module.DB = os.path.join(self.temp.name, 'remote.db')
        module.app.config['TESTING'] = True
        module.init_db()
        with self.connection() as con:
            remote_labs.migrate(con)
            for uid in (2, 3):
                con.execute("INSERT INTO users(id,name,email,role) VALUES(?,?,?,'participante')",
                            (uid, f'Participante {uid}', f'{uid}@example.invalid'))
            for mid in (1, 2):
                con.execute('INSERT INTO remote_machines(id,name,token_hash,last_seen) VALUES(?,?,?,?)',
                            (mid, f'VM {mid}', self.digest(mid), int(time.time())))
        self.client = module.app.test_client()
        self.agent = module.app.test_client()
        module.RATE_BUCKETS.clear()
        self.as_user(2)

    def tearDown(self):
        module.DB = self.old_db
        self.temp.cleanup()

    def connection(self):
        return closing_connection(module.DB)

    @staticmethod
    def token(mid=1):
        return f'test-agent-{mid}-' + 'a' * 40

    def digest(self, mid):
        return hashlib.sha256(self.token(mid).encode()).hexdigest()

    def as_user(self, uid):
        with self.client.session_transaction() as sess:
            sess.clear()
            sess.update(user_id=uid, csrf='remote-csrf')

    def post(self, path, **data):
        return self.client.post(path, data={'csrf_token': 'remote-csrf', **data})

    def poll(self, result=None, mid=1):
        return self.agent.post('/api/lab-agent/poll', json={'result': result},
                               headers={'Authorization': 'Bearer ' + self.token(mid)})

    def start(self):
        response = self.post('/remote-labs/start', consent='yes')
        self.assertEqual(response.status_code, 302)
        return int(response.location.rsplit('/', 1)[1])

    def command(self, sid, text='printf hello', key=None):
        return self.post(f'/remote-labs/{sid}/commands', command=text,
                         request_key=key or str(uuid.uuid4()))

    def scalar(self, sql):
        with closing(sqlite3.connect(module.DB)) as con:
            return con.execute(sql).fetchone()[0]

    def test_agent_authentication_cannot_use_browser_session(self):
        self.assertEqual(self.client.post('/api/lab-agent/poll', json={}).status_code, 401)
        self.assertEqual(self.agent.post('/api/lab-agent/poll', json={},
                         headers={'Authorization': 'Bearer ' + 'x' * 40}).status_code, 401)
        self.assertEqual(self.poll().get_json()['state'], 'idle')
        self.assertEqual(self.client.post('/remote-labs/start', data={'consent': 'yes'}).status_code, 400)
        self.assertEqual(self.agent.post('/api/lab-agent/poll', json=[],
                         headers={'Authorization': 'Bearer ' + self.token()}).status_code, 400)

    def test_roundtrip_is_observable_and_results_are_idempotent(self):
        sid = self.start()
        self.assertEqual(self.command(sid).status_code, 302)
        data = self.poll().get_json()
        self.assertEqual(data['state'], 'active')
        job = data['job']
        self.assertEqual(job['command'], 'printf hello')
        self.assertIsNone(self.poll().get_json()['job'])
        result = dict(command_id=job['command_id'], lease_token=job['lease_token'], output='hello', exit_code=0)
        self.assertEqual(self.poll(result).status_code, 200)
        result['output'] = 'replay must not overwrite history'
        self.assertEqual(self.poll(result).status_code, 200)
        events = self.client.get(f'/remote-labs/{sid}/events')
        self.assertEqual(events.get_json()['commands'][0]['output'], 'hello')
        self.assertNotIn(b'lease_token', events.data)
        self.assertNotIn(self.digest(1).encode(), events.data)
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM attempts'), 0)

    def test_ownership_observer_and_private_notes(self):
        sid = self.start()
        self.command(sid, 'echo observation')
        self.as_user(1)
        self.assertEqual(self.post(f'/remote-labs/{sid}/notes', body='Private reviewer note').status_code, 302)
        self.assertIn(b'Private reviewer note', self.client.get(f'/remote-labs/{sid}/events').data)
        self.assertEqual(self.command(sid, 'echo mentor cannot execute').status_code, 403)
        self.as_user(2)
        self.assertNotIn(b'Private reviewer note', self.client.get(f'/remote-labs/{sid}/events').data)
        self.assertEqual(self.post(f'/remote-labs/{sid}/notes', body='forbidden').status_code, 403)
        self.as_user(3)
        for url in (f'/remote-labs/{sid}', f'/remote-labs/{sid}/events'):
            self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.command(sid).status_code, 403)
        self.assertEqual(self.post(f'/remote-labs/{sid}/end').status_code, 403)

    def test_start_dedup_capacity_and_consent(self):
        self.assertEqual(self.post('/remote-labs/start').status_code, 400)
        sid = self.start()
        self.assertEqual(self.start(), sid)
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM remote_sessions'), 1)
        self.as_user(3)
        other = self.start()
        self.assertNotEqual(sid, other)
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM remote_machines WHERE status='allocated'"), 2)
        self.post(f'/remote-labs/{other}/end')
        self.assertEqual(self.post('/remote-labs/start', consent='yes').status_code, 409)

    def test_concurrent_starts_reserve_one_machine_once(self):
        with self.connection() as con:
            con.execute("UPDATE remote_machines SET status='retired' WHERE id=2")

        def start_person(uid):
            client = module.app.test_client()
            with client.session_transaction() as sess:
                sess.update(user_id=uid, csrf='parallel-csrf')
            return client.post('/remote-labs/start', data={'csrf_token': 'parallel-csrf', 'consent': 'yes'}).status_code

        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses = list(pool.map(start_person, (2, 3)))
        self.assertEqual(sorted(statuses), [302, 409])
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM remote_sessions'), 1)

    def test_command_duplicate_conflict_and_pending_quota(self):
        sid = self.start()
        key = str(uuid.uuid4())
        self.assertEqual(self.command(sid, key=key).status_code, 302)
        self.assertEqual(self.command(sid, key=key).status_code, 302)
        self.assertEqual(self.command(sid, 'changed', key=key).status_code, 409)
        self.assertEqual(self.command(sid, 'second').status_code, 409)
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM remote_commands'), 1)
        self.assertEqual(self.command(sid, key='bad').status_code, 400)
        self.assertEqual(self.command(sid, 'x' * 1001).status_code, 400)

    def test_forged_ack_cross_machine_and_validation(self):
        sid = self.start()
        self.command(sid)
        job = self.poll().get_json()['job']
        result = dict(command_id=job['command_id'], lease_token=job['lease_token'], output='hello', exit_code=0)
        self.assertEqual(self.poll(result, mid=2).status_code, 409)
        forged = dict(result, lease_token='wrong')
        self.assertEqual(self.poll(forged).status_code, 409)
        for changed in (dict(result, command_id=2**64), dict(result, output='a' * 16001),
                        dict(result, exit_code=True), dict(result, output={}), dict(result, extra='field'),
                        dict(result, lease_token='\ud800'), dict(result, output='\ud800')):
            self.assertEqual(self.poll(changed).status_code, 400)
        self.assertEqual(self.scalar('SELECT status FROM remote_commands'), 'running')

    def test_expiry_retires_machine_and_blocks_further_commands(self):
        sid = self.start()
        self.command(sid)
        self.poll()
        with self.connection() as con:
            con.execute('UPDATE remote_sessions SET expires_at=? WHERE id=?', (int(time.time()) - 1, sid))
        self.assertEqual(self.poll().get_json()['state'], 'retired')
        self.assertEqual(self.scalar('SELECT status FROM remote_sessions'), 'expired')
        self.assertEqual(self.scalar('SELECT status FROM remote_commands'), 'interrupted')
        self.assertEqual(self.command(sid, 'after expiry').status_code, 409)
        self.assertEqual(self.scalar('SELECT status FROM remote_machines WHERE id=1'), 'retired')

    def test_lost_ack_is_never_executed_again(self):
        sid = self.start()
        self.command(sid)
        job = self.poll().get_json()['job']
        with self.connection() as con:
            con.execute('UPDATE remote_commands SET started_at=?', (int(time.time()) - 46,))
        self.assertIsNone(self.poll().get_json()['job'])
        self.assertEqual(self.scalar('SELECT status FROM remote_commands'), 'interrupted')
        result = dict(command_id=job['command_id'], lease_token=job['lease_token'], output='late output', exit_code=0)
        self.assertEqual(self.poll(result).status_code, 200)
        self.assertEqual(self.scalar('SELECT output FROM remote_commands'), '')

    def test_offline_workers_and_end_are_enforced(self):
        with self.connection() as con:
            con.execute('UPDATE remote_machines SET last_seen=0')
        self.assertEqual(self.post('/remote-labs/start', consent='yes').status_code, 409)
        self.poll()
        sid = self.start()
        self.command(sid)
        self.assertEqual(self.post(f'/remote-labs/{sid}/end').status_code, 302)
        self.assertEqual(self.post(f'/remote-labs/{sid}/end').status_code, 302)
        self.assertEqual(self.scalar('SELECT status FROM remote_commands'), 'interrupted')
        self.assertEqual(self.poll().get_json()['state'], 'retired')
        self.assertEqual(self.command(sid).status_code, 409)


class closing_connection:
    def __init__(self, path):
        self.con = sqlite3.connect(path)

    def __enter__(self):
        return self.con

    def __exit__(self, typ, value, traceback):
        try:
            if typ is None:
                self.con.commit()
            else:
                self.con.rollback()
        finally:
            self.con.close()


if __name__ == '__main__':
    unittest.main()
