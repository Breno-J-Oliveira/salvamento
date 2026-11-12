import os
import sqlite3
import tempfile
import unittest
from contextlib import closing

os.environ.setdefault('SECRET_KEY','candidate-qa-only')
import app as module
import recruitment


class CandidateUpgradeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.old=module.DB
        module.DB=os.path.join(self.temp.name,'candidate.db');module.app.config['TESTING']=True
        module.init_db();module.RATE_BUCKETS.clear();self.client=module.app.test_client()
        with closing(sqlite3.connect(module.DB)) as c,c:
            c.execute("INSERT INTO users(id,name,email,password,role) VALUES(2,'Candidate','candidate@test.local','unused','participante')")
            c.execute("INSERT INTO users(id,name,email,password,role) VALUES(3,'Other','other@test.local','unused','participante')")
            for title,side,modality,active in [('SOC Alpha','Blue Team','Remoto',1),('AppSec Beta','Red Team','Presencial',1),('Hidden Alpha','Blue Team','Remoto',0)]:
                c.execute('INSERT INTO jobs(title,company,description,side,min_points,active,modality,status) VALUES(?,?,?,?,0,?,?,?)',(title,'Fictícia','Logs e segurança',side,active,modality,'published' if active else 'paused'))
            version=recruitment.create_version(c,1,[dict(id='evidence',label='Evidência original',type='select',required=True,options=['RESPOSTA_PUBLICA','GABARITO_PRIVADO'],correct_answer='GABARITO_PRIVADO')],1)
            c.execute('UPDATE jobs SET current_form_version=? WHERE id=1',(version,))
            stamp=1794450600 # 12/11/2026 02:30 UTC = 11/11/2026 23:30 Brasília
            for uid in (2,3):
                aid=c.execute("INSERT INTO applications(job_id,user_id,created_at,status,form_version,updated_at,submitted_at,notes,feedback) VALUES(?,?,?,'submitted',?,?,?,'NOTA_PRIVADA','Feedback público')",(1,uid,stamp,version,stamp,stamp)).lastrowid
                recruitment.write_answers(c,aid,recruitment.load_questions(c,version),{'evidence':'RESPOSTA_PUBLICA'})
                c.execute("INSERT INTO application_history(application_id,actor_id,status,created_at) VALUES(?,1,'submitted',?)",(aid,stamp))
        self.as_user(2)

    def tearDown(self):
        module.DB=self.old;self.temp.cleanup()

    def as_user(self,uid):
        with self.client.session_transaction() as s:s.clear();s.update(user_id=uid,csrf='test')

    def test_combined_vacancy_filters_and_literal_search(self):
        response=self.client.get('/opportunities?q=Alpha&side=Blue+Team&modality=Remoto')
        self.assertEqual(response.status_code,200)
        self.assertIn(b'SOC Alpha',response.data);self.assertNotIn(b'AppSec Beta',response.data);self.assertNotIn(b'Hidden Alpha',response.data)
        self.assertIn(b'value="Alpha"',response.data)
        empty=self.client.get('/opportunities?q=%27%20OR%201%3D1--')
        self.assertEqual(empty.status_code,200);self.assertIn('Nenhuma vaga corresponde aos filtros'.encode(),empty.data)

    def test_invalid_filters_are_controlled(self):
        for query in ['side=invalid','modality=invalid','q='+('a'*121)]:
            self.assertEqual(self.client.get('/opportunities?'+query).status_code,400)

    def test_dates_progress_and_history_do_not_expose_internal_data(self):
        response=self.client.get('/my-applications')
        self.assertEqual(response.status_code,200)
        self.assertIn(b'11/11/2026',response.data);self.assertIn(b'23:30',response.data)
        self.assertIn('avaliação prática ainda não iniciada'.encode(),response.data)
        self.assertIn('Histórico desta candidatura'.encode(),response.data)
        for secret in [b'NOTA_PRIVADA',b'GABARITO_PRIVADO',b'other@test.local']:self.assertNotIn(secret,response.data)

    def test_receipt_uses_owned_snapshot_without_answer_keys(self):
        with closing(sqlite3.connect(module.DB)) as c,c:
            new=recruitment.create_version(c,1,[dict(id='evidence',label='Pergunta posterior',type='text',required=False,options=[])],1)
            c.execute('UPDATE jobs SET current_form_version=? WHERE id=1',(new,))
        response=self.client.get('/my-applications/1/receipt')
        self.assertEqual(response.status_code,200)
        self.assertIn('Evidência original'.encode(),response.data);self.assertIn(b'RESPOSTA_PUBLICA',response.data)
        for secret in [b'NOTA_PRIVADA',b'GABARITO_PRIVADO',b'Pergunta posterior']:self.assertNotIn(secret,response.data)
        self.assertEqual(response.headers['Cache-Control'],'no-store')

    def test_receipt_denies_other_candidate_mentor_and_anonymous(self):
        self.assertEqual(self.client.get('/my-applications/2/receipt').status_code,404)
        self.as_user(1);self.assertEqual(self.client.get('/my-applications/1/receipt').status_code,403)
        with self.client.session_transaction() as s:s.clear()
        self.assertEqual(self.client.get('/my-applications/1/receipt').status_code,302)

    def test_draft_receipt_and_escaping(self):
        with closing(sqlite3.connect(module.DB)) as c,c:
            c.execute("UPDATE applications SET status='draft',submitted_at=NULL WHERE id=1")
            c.execute("UPDATE application_answers SET value='<script>alert(1)</script>' WHERE application_id=1")
        response=self.client.get('/my-applications/1/receipt')
        self.assertEqual(response.status_code,200)
        self.assertIn('ainda não foi enviado'.encode(),response.data)
        self.assertNotIn(b'<script>alert(1)</script>',response.data);self.assertIn(b'&lt;script&gt;',response.data)

    def test_private_status_filter_and_deadline_do_not_cancel_submitted(self):
        with closing(sqlite3.connect(module.DB)) as c,c:
            c.execute('UPDATE jobs SET deadline_at=1 WHERE id=1')
        response=self.client.get('/my-applications?status=submitted')
        self.assertEqual(response.status_code,200)
        self.assertIn('isso não cancela uma candidatura já enviada'.encode(),response.data)
        self.assertIn(b'1 candidatura(s) exibida(s) de 1',response.data)
        self.assertNotIn(b'Other',response.data)
        empty=self.client.get('/my-applications?status=selected')
        self.assertEqual(empty.status_code,200);self.assertIn('Nenhuma candidatura nesta etapa'.encode(),empty.data)
        self.assertEqual(self.client.get('/my-applications?status=invalid').status_code,400)


if __name__=='__main__':unittest.main()
