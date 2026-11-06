import json
import re
from html import unescape
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
os.environ.setdefault('SECRET_KEY','test-only')
import app as module
import recruitment

class RecruitmentTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.old=module.DB
        module.DB=os.path.join(self.temp.name,'test.db');module.app.config['TESTING']=True
        module.RATE_BUCKETS.clear();module.init_db();self.client=module.app.test_client()
        with closing(sqlite3.connect(module.DB)) as con,con:
            con.execute("INSERT INTO users(name,email,password,role) VALUES('Candidate','candidate@example.test','unused','participante')")
            con.execute("INSERT INTO users(name,email,password,role) VALUES('Other','other@example.test','unused','participante')")
            con.execute("INSERT INTO jobs(title,company,description,side,min_points,active) VALUES('SOC Junior','Equipe','Descrição completa da vaga','Blue Team',0,1)")
            con.execute("INSERT INTO jobs(title,company,description,side,min_points,active) VALUES('AppSec','Equipe','Descrição completa da vaga','Red Team',0,1)")
    def tearDown(self):module.DB=self.old;self.temp.cleanup()
    def as_user(self,uid=2):
        with self.client.session_transaction() as s:s.update(user_id=uid,csrf='test')
    def token(self,jid=1):
        response=self.client.get(f'/applications/{jid}/form')
        match=re.search(r'name="form_token" value="([^"]+)"',response.get_data(as_text=True))
        self.assertIsNotNone(match)
        return unescape(match.group(1))
    def post(self,path,data=None):
        data=dict(data or {})
        if 'questions_json' in data:
            questions=json.loads(data.pop('questions_json'))
            data['question_count']=str(len(questions))
            for i,q in enumerate(questions):
                prefix=f'question_{i}_'
                data.update({prefix+'id':q['id'],prefix+'label':q['label'],prefix+'type':q['type'],prefix+'required':'1' if q['required'] else '0',prefix+'option':q.get('options',[])})
        if re.fullmatch(r'/applications/\d+/form',path) and 'form_token' not in data:
            data['form_token']=self.token(int(path.split('/')[2]))
        with self.client.session_transaction() as s:s['csrf']='test'
        return self.client.post(path,data={'csrf_token':'test',**data})
    def rows(self,sql,args=()):
        with closing(sqlite3.connect(module.DB)) as con,con:return con.execute(sql,args).fetchall()
    def write(self,sql,args=()):
        with closing(sqlite3.connect(module.DB)) as con,con:con.execute(sql,args)
    def draft(self,jid=1):
        self.as_user();return self.post(f'/applications/{jid}/form',{'action':'review','q_availability':'Manhã','q_experience':'Análise de logs acadêmicos','q_portfolio':''})

    def test_public_jobs_and_paused_hidden(self):
        self.assertEqual(self.client.get('/opportunities').status_code,200)
        self.assertEqual(self.client.get('/opportunities/1').status_code,200)
        self.write('UPDATE jobs SET active=0 WHERE id=1')
        self.assertEqual(self.client.get('/opportunities/1').status_code,404)
        self.assertNotIn(b'SOC Junior',self.client.get('/opportunities').data)
    def test_auth_return_and_roles(self):
        r=self.client.get('/applications/1/form');self.assertEqual(r.status_code,302);self.assertIn('next=/applications/1/form',r.location)
        self.as_user(1);self.assertEqual(self.client.get('/applications/1/form').status_code,403)
        self.as_user();self.assertEqual(self.client.get('/admin').status_code,403)
    def test_missing_required_unknown_fields_and_invalid_url(self):
        self.as_user()
        for data in [{'action':'review'}, {'action':'save','q_unknown':'x'}, {'action':'save','q_portfolio':'https://[invalid'}, {'action':'save','q_portfolio':'javascript:alert(1)'}]:
            self.assertEqual(self.post('/applications/1/form',data).status_code,400)
        self.assertFalse(self.rows('SELECT id FROM applications'))
    def test_draft_review_submit_idempotent(self):
        self.as_user();self.assertEqual(self.post('/applications/1/form',{'action':'save','q_availability':'Manhã'}).status_code,302)
        self.assertEqual(self.rows('SELECT status FROM applications'),[('draft',)])
        self.assertEqual(self.client.get('/applications/1/review').status_code,302)
        self.assertEqual(self.draft().status_code,302)
        self.assertEqual(self.client.get('/applications/1/review').status_code,200)
        for _ in range(2):self.assertEqual(self.post('/applications/1/review').status_code,302)
        self.assertEqual(self.rows('SELECT status FROM applications'),[('submitted',)])
        self.assertEqual(self.rows('SELECT COUNT(*) FROM application_history'),[(1,)])
    def test_two_vacancies_and_snapshot_preserved(self):
        self.draft();self.assertNotEqual(recruitment.defaults('Red Team'),recruitment.defaults('Blue Team'))
        before=self.rows('SELECT form_version FROM applications')[0][0]
        self.as_user(1);questions=[dict(id='newquestion',label='Uma nova pergunta?',type='text',required=True,options=[])]
        self.assertEqual(self.post('/admin/jobs/1/form',{'questions_json':json.dumps(questions)}).status_code,302)
        self.as_user();self.assertIn(b'q_experience',self.client.get('/applications/1/form').data)
        self.assertEqual(self.rows('SELECT form_version FROM applications')[0][0],before)
        self.as_user(3);response=self.client.get('/applications/1/form');self.assertIn(b'q_newquestion',response.data);self.assertNotIn(b'q_experience',response.data)
    def test_pause_prevents_submission_preserves_draft(self):
        self.draft();self.write('UPDATE jobs SET active=0 WHERE id=1')
        self.assertEqual(self.post('/applications/1/review').status_code,400)
        self.assertEqual(self.rows('SELECT status FROM applications'),[('draft',)])
        self.assertEqual(self.post('/applications/1/form',{'action':'save'}).status_code,400)
    def test_ownership_and_private_notes(self):
        self.draft();self.post('/applications/1/review');self.as_user(1)
        self.assertEqual(self.post('/admin/applications/1',{'status':'interview','notes':'PRIVATE_SENTINEL','feedback':'PUBLIC_FEEDBACK'}).status_code,302)
        self.as_user();response=self.client.get('/my-applications');self.assertIn(b'PUBLIC_FEEDBACK',response.data);self.assertNotIn(b'PRIVATE_SENTINEL',response.data)
        self.assertEqual(self.client.get('/admin/applications/1').status_code,403)
        self.as_user(3);self.assertNotIn(b'PUBLIC_FEEDBACK',self.client.get('/my-applications').data)
        self.assertEqual(self.client.get('/applications/1/review').status_code,302)
    def test_admin_does_not_see_drafts_and_legacy_cannot_bypass(self):
        self.draft();self.as_user(1)
        self.assertEqual(self.client.get('/admin/applications/1').status_code,404)
        self.assertNotIn(b'Candidate',self.client.get('/jobs').data)
        self.as_user(3);response=self.post('/jobs/1/apply');self.assertEqual(response.location,'/applications/1/form')
        self.assertEqual(self.rows('SELECT COUNT(*) FROM applications'),[(1,)])
    def test_questions_schema_validation(self):
        for raw in ['{}','[]','[null]',json.dumps([dict(id='same',label='Question',type='text'),dict(id='same',label='Question',type='text')]),json.dumps([dict(id='x',label='Question',type='select',options=[])]),json.dumps([dict(id='x',label='Question',type='text',required='yes')])]:
            with self.assertRaises(ValueError):recruitment.validate_questions(json.loads(raw))
    def test_safe_next_and_successful_login(self):
        for value in ['https://evil.test','//evil.test','/%5cevil.test','/x%0d%0aLocation:evil']:
            self.assertEqual(recruitment.safe_next(value),'')
        self.assertEqual(recruitment.safe_next('/applications/1/form'),'/applications/1/form')
        response=self.post('/login?next=/applications/1/form',{'email':'mentor@cti.local','password':'mentor123'})
        self.assertEqual(response.location,'/applications/1/form')
    def test_concurrent_confirmation_creates_one_history_event(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        self.draft()
        barrier=Barrier(2)
        def confirm():
            client=module.app.test_client()
            with client.session_transaction() as sess:sess.update(user_id=2,csrf='concurrent')
            barrier.wait(timeout=5)
            return client.post('/applications/1/review',data={'csrf_token':'concurrent'}).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sorted(pool.map(lambda _:confirm(),range(2))),[302,302])
        self.assertEqual(self.rows('SELECT status FROM applications'),[('submitted',)])
        self.assertEqual(self.rows('SELECT COUNT(*) FROM application_history'),[(1,)])

    def test_signed_first_visit_preserves_question_label_across_admin_edit(self):
        self.as_user();token=self.token()
        self.as_user(1)
        questions=recruitment.defaults('Blue Team')
        questions[1]['label']='Pergunta completamente diferente, mesmo identificador'
        self.post('/admin/jobs/1/form',{'questions_json':json.dumps(questions)})
        self.as_user()
        response=self.post('/applications/1/form',{'form_token':token,'action':'review','q_availability':'Manhã','q_experience':'Minha resposta à pergunta original'})
        self.assertEqual(response.status_code,302)
        with closing(sqlite3.connect(module.DB)) as con:
            snapshot=recruitment.load_questions(con,self.rows('SELECT form_version FROM applications')[0][0])
        self.assertEqual(snapshot[1]['label'],recruitment.defaults('Blue Team')[1]['label'])
        self.assertNotEqual(snapshot[1]['label'],questions[1]['label'])
    def test_signed_token_rejects_tampering_wrong_user_wrong_job_and_missing(self):
        self.as_user();token=self.token()
        data={'action':'save','form_token':token+'tampered'}
        self.assertEqual(self.post('/applications/1/form',data).status_code,400)
        self.assertEqual(self.post('/applications/2/form',{'action':'save','form_token':token}).status_code,400)
        self.as_user(3)
        self.assertEqual(self.post('/applications/1/form',{'action':'save','form_token':token}).status_code,400)
        self.assertEqual(self.post('/applications/1/form',{'action':'save','form_token':''}).status_code,400)
        self.assertEqual(self.rows('SELECT COUNT(*) FROM applications'),[(0,)])

    def test_json_legacy_migrates_into_relational_questions_and_answers(self):
        path=os.path.join(self.temp.name,'legacy-forms.db')
        with closing(sqlite3.connect(path)) as con,con:
            con.execute('PRAGMA foreign_keys=ON')
            con.executescript("CREATE TABLE users(id INTEGER PRIMARY KEY); INSERT INTO users VALUES(1); CREATE TABLE jobs(id INTEGER PRIMARY KEY,side TEXT); INSERT INTO jobs VALUES(1,'Blue Team'); CREATE TABLE applications(id INTEGER PRIMARY KEY,job_id INTEGER,user_id INTEGER,created_at INTEGER,form_version INTEGER,questions_snapshot TEXT,answers_json TEXT); CREATE TABLE job_form_versions(id INTEGER PRIMARY KEY,job_id INTEGER,questions_json TEXT NOT NULL,created_at INTEGER,created_by INTEGER);")
            questions=[dict(id='experience',label='Pergunta histórica?',type='textarea',required=True,options=[])]
            con.execute('INSERT INTO job_form_versions VALUES(1,1,?,1,1)',(json.dumps(questions),))
            con.execute('INSERT INTO applications VALUES(1,1,1,1,1,?,?)',(json.dumps(questions),json.dumps({'experience':'Resposta histórica preservada'})))
            recruitment.migrate(con);con.commit();recruitment.migrate(con)
            version=con.execute('SELECT form_version FROM applications').fetchone()[0]
            self.assertEqual(recruitment.load_questions(con,version)[0]['label'],'Pergunta histórica?')
            self.assertEqual(recruitment.read_answers(con,1,recruitment.load_questions(con,version)),{'experience':'Resposta histórica preservada'})
            self.assertFalse(con.execute('PRAGMA foreign_key_check').fetchall())
            self.assertNotIn('questions_json',{r[1] for r in con.execute('PRAGMA table_info(job_form_versions)')})

    def test_migration_idempotent(self):
        module.init_db();module.init_db();self.assertEqual(self.rows('SELECT COUNT(*) FROM jobs'),[(2,)])

if __name__=='__main__':unittest.main()
