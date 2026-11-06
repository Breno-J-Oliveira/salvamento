import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import app as module

class MaturityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.old=module.DB
        module.DB=os.path.join(self.temp.name,'mature.db');module.app.config['TESTING']=True
        module.RATE_BUCKETS.clear();module.init_db();self.client=module.app.test_client()
        with self.client.session_transaction() as s:s.update(user_id=1,csrf='token')
    def tearDown(self):module.DB=self.old;self.temp.cleanup()
    def test_job_state_replay_is_idempotent(self):
        con=sqlite3.connect(module.DB)
        con.execute("INSERT INTO jobs(title,company,description,side,min_points) VALUES('SOC','Empresa','Descrição da oportunidade','Blue Team',0)")
        con.commit();con.close()
        for _ in range(2):self.assertEqual(self.client.post('/jobs/1/toggle',data={'csrf_token':'token','active':'0'}).status_code,302)
        con=sqlite3.connect(module.DB)
        try:self.assertEqual(con.execute('SELECT active FROM jobs').fetchone()[0],0)
        finally:con.close()
        self.assertEqual(self.client.post('/jobs/1/toggle',data={'csrf_token':'token','active':'x'}).status_code,400)
    def test_busy_database_has_retry_response_without_details(self):
        with patch.object(module,'db',side_effect=sqlite3.OperationalError('database is locked secret sentinel')):
            response=self.client.get('/')
        self.assertEqual(response.status_code,503)
        self.assertEqual(response.headers['Retry-After'],'5')
        self.assertNotIn(b'sentinel',response.data)
    def test_database_failure_is_not_reported_as_success(self):
        with patch.object(module,'db',side_effect=sqlite3.OperationalError('internal sentinel')):
            response=self.client.get('/')
        self.assertEqual(response.status_code,500);self.assertNotIn(b'sentinel',response.data)
    def test_mentor_dossier_title_contains_no_report_content(self):
        con=sqlite3.connect(module.DB)
        con.execute("INSERT INTO users(id,name,email,role) VALUES(2,'Pessoa','qa@example.com','participante')")
        con.execute("INSERT INTO writeups VALUES(2,1,'Relato privado do participante',1)")
        con.commit();con.close()
        response=self.client.get('/participante/2')
        title=response.data.split(b'<title>')[1].split(b'</title>')[0]
        self.assertNotIn(b'Relato privado',title);self.assertNotIn(b'<section',title)
        self.assertIn(b'Relato privado',response.data)

if __name__=='__main__':unittest.main()
