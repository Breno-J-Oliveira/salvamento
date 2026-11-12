import os
import sqlite3
import tempfile
import time
import unittest
from contextlib import closing
from unittest.mock import patch
os.environ.setdefault('SECRET_KEY', 'test-only-lab-workspace')
import app as module


class LaboratoryWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old = module.DB
        module.DB = os.path.join(self.temp.name, 'test.db')
        module.app.config['TESTING'] = True
        module.init_db()
        self.client = module.app.test_client()
        with closing(sqlite3.connect(module.DB)) as con, con:
            con.execute("INSERT INTO users(id,name,email,password,role) VALUES(2,'QA','qa@example.test','unused','participante')")
            con.execute("INSERT INTO users(id,name,email,password,role) VALUES(3,'Other','other@example.test','unused','participante')")
            self.cid = con.execute("SELECT id FROM challenges WHERE image='cti-lab/incident-01'").fetchone()[0]
            for uid, expires, port in [(2,int(time.time())+1800,22001),(3,int(time.time())+1800,22002),(2,int(time.time())-1,22003)]:
                con.execute("INSERT INTO instances(user_id,challenge_id,container,port,started_at,expires_at,active) VALUES(?,?,?,?,?,?,1)",(uid,self.cid,'fake-'+str(port),port,int(time.time()),expires))

    def tearDown(self):
        module.DB = self.old
        self.temp.cleanup()

    def test_requires_login_and_distinguishes_consoles_without_private_instances(self):
        self.assertEqual(self.client.get('/labs').status_code,302)
        with self.client.session_transaction() as session:session['user_id']=1
        response = self.client.get('/labs')
        self.assertEqual(response.status_code,200)
        html=response.get_data(as_text=True)
        self.assertIn('Investigação de incidente',html)
        self.assertIn('Exploração de aplicação web',html)
        self.assertNotIn('Instância registrada',html)
        self.assertNotIn('22002',html)
        self.assertLess(html.index('Incidente em andamento'),html.index('Intranet esquecida'))

    def test_only_current_users_unexpired_instances_are_summarized(self):
        with self.client.session_transaction() as session:session['user_id']=2
        with patch.object(module.orch,'status') as status:
            response=self.client.get('/labs')
            status.assert_not_called()
        html=response.get_data(as_text=True)
        self.assertIn('1 de 2',html)
        self.assertIn('Gerenciar meu ambiente',html)
        self.assertIn('data-expiry',html)
        self.assertNotIn('22002',html)
        self.assertIn('O estado real do Docker é confirmado',html)

    def test_completed_badge_belongs_to_logged_user(self):
        with closing(sqlite3.connect(module.DB)) as con,con:
            con.execute('INSERT INTO attempts(user_id,challenge_id,correct,created_at) VALUES(?,?,1,?)',(3,self.cid,int(time.time())))
        with self.client.session_transaction() as session:session['user_id']=2
        self.assertNotIn('Concluído',self.client.get('/labs').get_data(as_text=True))
        with self.client.session_transaction() as session:session['user_id']=3
        self.assertIn('Concluído',self.client.get('/labs').get_data(as_text=True))


if __name__ == '__main__':unittest.main()
