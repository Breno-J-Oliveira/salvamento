import os
import sqlite3
import tempfile
import unittest
import app as module

class LearningTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.old=module.DB
        module.DB=os.path.join(self.temp.name,'learning.db')
        module.app.config['TESTING']=True;module.RATE_BUCKETS.clear();module.init_db()
        con=sqlite3.connect(module.DB)
        con.execute("INSERT INTO users(id,name,email,password,role,team) VALUES(2,'QA','qa@example.com','unused','participante','QA')")
        con.commit();con.close();self.client=module.app.test_client()
        with self.client.session_transaction() as s:s.update(user_id=2,csrf='token')
    def tearDown(self):module.DB=self.old;self.temp.cleanup()
    def solve(self):
        con=sqlite3.connect(module.DB);con.execute('INSERT INTO attempts(user_id,challenge_id,correct,created_at) VALUES(2,1,1,123)');con.commit();con.close()
    def post(self,content):return self.client.post('/writeups/1',data={'csrf_token':'token','content':content})
    def test_progress_renders_empty_and_solved(self):
        self.assertEqual(self.client.get('/progress').status_code,200);self.solve()
        self.assertIn(b'Boas-vindas',self.client.get('/progress').data)
    def test_cannot_write_unsolved_or_alien_solution(self):
        self.assertEqual(self.post('Relato detalhado que ainda nao possui solucao.').status_code,403)
    def test_writeup_validated_upserted_and_escaped(self):
        self.solve();self.assertEqual(self.post('curto').status_code,400)
        self.assertEqual(self.post('x'*6001).status_code,400)
        text='<script>alert(1)</script> Relato com evidencias de investigacao.'
        self.assertEqual(self.post(text).status_code,302);self.post(text+' Atualizado')
        page=self.client.get('/progress');self.assertNotIn(b'<script>alert(1)</script>',page.data)
        con=sqlite3.connect(module.DB)
        try:self.assertEqual(con.execute('SELECT COUNT(*) FROM writeups').fetchone()[0],1)
        finally:con.close()
    def test_private_progress_requires_authentication(self):
        self.assertEqual(module.app.test_client().get('/progress').status_code,302)

if __name__=='__main__':unittest.main()
