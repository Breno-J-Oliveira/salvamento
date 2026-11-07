import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from unittest.mock import patch
import app as module


class ApplicationHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.old=module.DB
        module.DB=os.path.join(self.temp.name,'history.db')
        module.app.config['TESTING']=True;module.RATE_BUCKETS.clear()
        # Autenticação por senha é coberta em outra suíte; aqui usamos sessões sintéticas.
        with patch.object(module,'generate_password_hash',return_value='unused-history-test-hash'):
            module.init_db()
        with closing(sqlite3.connect(module.DB)) as con, con:
            con.execute("INSERT INTO users(id,name,email,role) VALUES(2,'Pessoa','candidate@example.test','participante')")
            con.execute("INSERT INTO users(id,name,email,role) VALUES(3,'<script>alert(1)</script>','reviewer@example.test','mentor')")
            con.execute("INSERT INTO jobs(id,title,company,description,side,min_points,active) VALUES(1,'SOC','Demo','Descrição sintética','Blue Team',0,1)")
            con.execute("INSERT INTO applications(id,job_id,user_id,status,created_at) VALUES(1,1,2,'review',1)")
        self.client=module.app.test_client();self.as_user(1)

    def tearDown(self):
        module.DB=self.old;self.temp.cleanup()

    def as_user(self,uid):
        with self.client.session_transaction() as s:s.clear();s.update(user_id=uid,csrf='token')

    def event(self,status,actor,created):
        with closing(sqlite3.connect(module.DB)) as con,con:
            con.execute('INSERT INTO application_history(application_id,actor_id,status,created_at) VALUES(1,?,?,?)',(actor,status,created))

    def page(self):return self.client.get('/admin/applications/1')

    def test_chronology_actor_and_utc_are_visible(self):
        self.event('interview',1,120);self.event('submitted',2,60)
        response=self.page();self.assertEqual(response.status_code,200)
        body=response.data.decode()
        history=body.split('Histórico de etapas',1)[1]
        self.assertLess(history.index('Enviada'),history.index('Entrevista'))
        self.assertIn('Pessoa · ID 2',history)
        self.assertIn('01/01/1970 00:01 UTC',history)
        self.assertIn('1970-01-01T00:01:00+00:00',history)

    def test_missing_actor_and_invalid_date_have_fallbacks(self):
        self.event('submitted',999,9223372036854775807)
        response=self.page();self.assertEqual(response.status_code,200)
        self.assertIn('Usuário indisponível · ID 999'.encode(),response.data)
        self.assertIn('Data indisponível'.encode(),response.data)

    def test_actor_name_is_escaped(self):
        self.event('review',3,120)
        response=self.page()
        self.assertNotIn(b'<script>alert(1)</script>',response.data)
        self.assertIn(b'&lt;script&gt;alert(1)&lt;/script&gt;',response.data)

    def test_participant_cannot_access_internal_history_and_draft_is_hidden(self):
        self.as_user(2);self.assertEqual(self.page().status_code,403)
        self.assertNotIn('Histórico de etapas'.encode(),self.client.get('/my-applications').data)
        self.as_user(1)
        with closing(sqlite3.connect(module.DB)) as con,con:con.execute("UPDATE applications SET status='draft' WHERE id=1")
        self.assertEqual(self.page().status_code,404)

    def test_empty_history_is_not_invented(self):
        response=self.page();self.assertEqual(response.status_code,200)
        self.assertIn('Nenhuma mudança de etapa registrada.'.encode(),response.data)


if __name__=='__main__':unittest.main()
