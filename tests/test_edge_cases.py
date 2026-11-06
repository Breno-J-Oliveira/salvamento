import concurrent.futures
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import app as module

class EdgeCases(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.old=module.DB
        module.DB=os.path.join(self.temp.name,'edge.db')
        module.app.config['TESTING']=True
        module.RATE_BUCKETS.clear()
        module.init_db()
        con=sqlite3.connect(module.DB)
        con.execute("INSERT INTO users(name,email,password,role,team) VALUES('QA','qa@example.com','unused','participante','QA')")
        con.commit();con.close()

    def tearDown(self):
        module.DB=self.old
        self.temp.cleanup()

    def client(self):
        client=module.app.test_client()
        with client.session_transaction() as s:
            s.update(user_id=2,role='participante',name='QA',csrf='token')
        return client

    def test_unicode_csrf_is_rejected_not_server_error(self):
        self.assertEqual(self.client().post('/profile',data={'csrf_token':'não-é-token'}).status_code,400)

    def test_concurrent_correct_submissions_only_award_once(self):
        def submit(_):
            return self.client().post('/challenge/1',data={'csrf_token':'token','flag':'CTF{bem_vindo_ao_purple_lab}'}).status_code
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            self.assertEqual(list(executor.map(submit,range(2))),[302,302])
        con=sqlite3.connect(module.DB)
        try:self.assertEqual(con.execute('SELECT COUNT(*) FROM attempts WHERE correct=1').fetchone()[0],1)
        finally:con.close()

    def test_per_user_capacity_prevents_launch(self):
        con=sqlite3.connect(module.DB)
        for cid in [91,92]:
            con.execute('INSERT INTO instances(user_id,challenge_id,active,expires_at) VALUES(2,?,1,9999999999)',(cid,))
        con.commit();con.close()
        with patch.object(module.orch,'start') as start:
            response=self.client().post('/challenge/2/start',data={'csrf_token':'token'})
            self.assertEqual(response.status_code,302)
            start.assert_not_called()

    def test_all_static_challenge_answers(self):
        client=self.client()
        for cid,flag in [(1,'CTF{bem_vindo_ao_purple_lab}'),(3,'CTF{base64_nao_e_criptografia}'),(4,'CTF{192.168.56.23}')]:
            self.assertEqual(client.post(f'/challenge/{cid}',data={'csrf_token':'token','flag':flag}).status_code,302)
        with module.app.test_request_context():
            self.assertEqual(module.stats()[0]['points'],300)

if __name__=='__main__':unittest.main()
