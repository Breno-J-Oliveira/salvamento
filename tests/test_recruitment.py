import json
import re
from html import unescape
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from werkzeug.security import generate_password_hash
from werkzeug.datastructures import MultiDict
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
                if 'correct_answer' in q:data[prefix+'correct']=q['correct_answer']
        if re.fullmatch(r'/applications/\d+/form',path) and 'form_token' not in data:
            data['form_token']=self.token(int(path.split('/')[2]))
        if re.fullmatch(r'/applications/\d+/review',path) and 'confirmation_token' not in data:
            response=self.client.get(path)
            match=re.search(r'name="confirmation_token" value="([^"]+)"',response.get_data(as_text=True))
            if match:data['confirmation_token']=unescape(match.group(1))
        if re.fullmatch(r'/admin/applications/\d+',path) and 'review_token' not in data:
            response=self.client.get(path)
            match=re.search(r'name="review_token" value="([^"]+)"',response.get_data(as_text=True))
            if match:data['review_token']=unescape(match.group(1))
        if re.fullmatch(r'/admin/jobs/\d+/form',path) and 'editor_token' not in data:
            response=self.client.get(path)
            match=re.search(r'name="editor_token" value="([^"]+)"',response.get_data(as_text=True))
            if match:data['editor_token']=unescape(match.group(1))
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
    def test_withdraw_application_preserves_evidence_and_is_idempotent(self):
        self.draft();self.post('/applications/1/review')
        before=self.rows('SELECT question_id,value FROM application_answers ORDER BY question_id,position')
        self.assertEqual(self.post('/my-applications/1/withdraw',{'confirm':'withdraw'}).status_code,302)
        self.assertEqual(self.post('/my-applications/1/withdraw',{'confirm':'withdraw'}).status_code,302)
        self.assertEqual(self.rows('SELECT status FROM applications'),[('withdrawn',)])
        self.assertEqual(self.rows('SELECT question_id,value FROM application_answers ORDER BY question_id,position'),before)
        self.assertEqual(self.rows("SELECT actor_id,status FROM application_history WHERE status='withdrawn'"),[(2,'withdrawn')])
        self.assertEqual(self.client.get('/my-applications/1/assessment').status_code,403)
        self.as_user(1)
        self.assertEqual(self.post('/admin/applications/1',{'status':'review','notes':'','feedback':''}).status_code,409)
        self.assertEqual(self.rows('SELECT status FROM applications'),[('withdrawn',)])
    def test_withdraw_requires_owner_confirmation_and_active_stage(self):
        self.draft()
        self.assertEqual(self.post('/my-applications/1/withdraw',{'confirm':'withdraw'}).status_code,409)
        self.post('/applications/1/review')
        self.assertEqual(self.post('/my-applications/1/withdraw',{}).status_code,400)
        self.as_user(3)
        self.assertEqual(self.post('/my-applications/1/withdraw',{'confirm':'withdraw'}).status_code,404)
        self.as_user(1)
        self.assertEqual(self.post('/my-applications/1/withdraw',{'confirm':'withdraw'}).status_code,403)
        self.as_user(2);self.write("UPDATE applications SET status='selected' WHERE id=1")
        self.assertEqual(self.post('/my-applications/1/withdraw',{'confirm':'withdraw'}).status_code,409)
        self.assertEqual(self.rows('SELECT status FROM applications'),[('selected',)])
    def test_stale_confirmation_requires_review_of_current_answers(self):
        self.draft()
        page=self.client.get('/applications/1/review').get_data(as_text=True)
        stale=unescape(re.search(r'name="confirmation_token" value="([^"]+)"',page).group(1))
        self.assertEqual(self.post('/applications/1/form',{'action':'save','q_availability':'Tarde','q_experience':'Outra experiência'}).status_code,302)
        self.assertEqual(self.post('/applications/1/review',{'confirmation_token':stale+'x'}).status_code,400)
        response=self.post('/applications/1/review',{'confirmation_token':stale})
        self.assertEqual(response.status_code,409)
        self.assertIn('Tarde',response.get_data(as_text=True))
        self.assertEqual(self.rows('SELECT status FROM applications'),[('draft',)])
        token=unescape(re.search(r'name="confirmation_token" value="([^"]+)"',response.get_data(as_text=True)).group(1))
        self.assertEqual(self.post('/applications/1/review',{'confirmation_token':token}).status_code,302)
        self.assertEqual(self.rows('SELECT status FROM applications'),[('submitted',)])
    def test_stale_confirmation_rejects_incomplete_current_draft(self):
        self.draft()
        page=self.client.get('/applications/1/review').get_data(as_text=True)
        stale=unescape(re.search(r'name="confirmation_token" value="([^"]+)"',page).group(1))
        self.post('/applications/1/form',{'action':'save','q_availability':'','q_experience':'Outra experiência'})
        response=self.post('/applications/1/review',{'confirmation_token':stale})
        self.assertEqual(response.status_code,409)
        self.assertEqual(self.rows('SELECT status FROM applications'),[('draft',)])
    def test_admin_cannot_withdraw_for_candidate(self):
        self.draft();self.post('/applications/1/review');self.as_user(1)
        self.assertEqual(self.post('/admin/applications/1',{'status':'withdrawn','notes':'','feedback':''}).status_code,409)
        self.assertEqual(self.rows('SELECT status FROM applications'),[('submitted',)])
    def test_concurrent_form_editors_preserve_newer_version(self):
        self.as_user(1)
        first=self.client.get('/admin/jobs/1/form').get_data(as_text=True)
        stale=unescape(re.search(r'name="editor_token" value="([^"]+)"',first).group(1))
        q1=[dict(id='q',label='Pergunta mais recente',type='select',required=True,options=['A','B'],correct_answer='A')]
        q2=[dict(id='q',label='Pergunta da outra aba',type='select',required=True,options=['X','Y'],correct_answer='Y')]
        self.assertEqual(self.post('/admin/jobs/1/form',{'questions_json':json.dumps(q1)}).status_code,302)
        version=self.rows('SELECT current_form_version FROM jobs WHERE id=1')[0][0]
        self.assertEqual(self.post('/admin/jobs/1/form',{'questions_json':json.dumps(q2),'editor_token':stale+'x'}).status_code,400)
        response=self.post('/admin/jobs/1/form',{'questions_json':json.dumps(q2),'editor_token':stale})
        self.assertEqual(response.status_code,409)
        self.assertIn('Pergunta da outra aba',response.get_data(as_text=True))
        self.assertIn('Y',response.get_data(as_text=True))
        self.assertEqual(self.rows('SELECT current_form_version FROM jobs WHERE id=1'),[(version,)])
        self.assertEqual(self.rows('SELECT label FROM form_questions WHERE version_id=?',(version,)),[('Pergunta mais recente',)])
        self.assertEqual(self.post('/admin/jobs/2/form',{'questions_json':json.dumps(q2),'editor_token':stale}).status_code,400)
    def test_concurrent_reviews_do_not_overwrite_and_keep_typed_fields(self):
        self.draft();self.post('/applications/1/review');self.as_user(1)
        other=self.client.application.test_client()
        with other.session_transaction() as session:session.update(user_id=1,csrf='test')
        page=other.get('/admin/applications/1').get_data(as_text=True)
        stale=unescape(re.search(r'name="review_token" value="([^"]+)"',page).group(1))
        self.assertEqual(other.post('/admin/applications/1',data={'csrf_token':'test','status':'review','review_token':stale+'x'}).status_code,400)
        self.assertEqual(self.post('/admin/applications/1',{'status':'interview','notes':'Primeiro avaliador','feedback':'Atualizado'}).status_code,302)
        response=other.post('/admin/applications/1',data={'csrf_token':'test','review_token':stale,'status':'review','notes':'Segundo avaliador','feedback':'Texto preservado'})
        self.assertEqual(response.status_code,409)
        self.assertIn('Segundo avaliador',response.get_data(as_text=True))
        self.assertIn('Texto preservado',response.get_data(as_text=True))
        self.assertEqual(self.rows('SELECT status,notes,feedback FROM applications'),[('interview','Primeiro avaliador','Atualizado')])
        self.assertEqual(self.rows('SELECT COUNT(*) FROM application_history'),[(2,)])
    def test_admin_does_not_see_drafts_and_legacy_cannot_bypass(self):
        self.draft();self.as_user(1)
        self.assertEqual(self.client.get('/admin/applications/1').status_code,404)
        self.assertNotIn(b'Candidate',self.client.get('/jobs').data)
        self.as_user(3);response=self.post('/jobs/1/apply');self.assertEqual(response.location,'/applications/1/form')
        self.assertEqual(self.rows('SELECT COUNT(*) FROM applications'),[(1,)])
    def test_questions_schema_validation(self):
        for raw in ['{}','[]','[null]',json.dumps([dict(id='same',label='Question',type='text'),dict(id='same',label='Question',type='text')]),json.dumps([dict(id='x',label='Question',type='select',options=[])]),json.dumps([dict(id='x',label='Question',type='text',required='yes')])]:
            with self.assertRaises(ValueError):recruitment.validate_questions(json.loads(raw))

    def test_choice_options_are_trimmed_and_duplicates_rejected(self):
        question=dict(id='area',label='Área preferida?',type='select',required=True,options=[' Ataque ', 'Defesa'])
        self.assertEqual(recruitment.validate_questions([question])[0]['options'],['Ataque','Defesa'])
        question['options']=['Ataque',' Ataque ']
        with self.assertRaises(ValueError):recruitment.validate_questions([question])

    def test_single_choice_rejects_multiple_submitted_values(self):
        self.as_user(1)
        question=dict(id='area',label='Área preferida?',type='select',required=True,options=['Ataque','Defesa'])
        self.assertEqual(self.post('/admin/jobs/1/form',{'questions_json':json.dumps([question])}).status_code,302)
        self.as_user(2);token=self.token()
        data=MultiDict([('csrf_token','test'),('form_token',token),('action','review'),('q_area','Ataque'),('q_area','Defesa')])
        self.assertEqual(self.client.post('/applications/1/form',data=data).status_code,400)
        self.assertEqual(self.rows('SELECT COUNT(*) FROM applications'),[(0,)])

    def test_optional_answer_key_is_versioned_private_and_scored_for_evaluator(self):
        from flask import template_rendered
        question=dict(id='area',label='Área?',type='select',required=True,options=['Ataque','Defesa'],correct_answer='Defesa')
        self.as_user(1);self.assertEqual(self.post('/admin/jobs/1/form',{'questions_json':json.dumps([question])}).status_code,302)
        self.as_user(2);captured=[]
        def capture(sender,template,context,**extra):captured.append((template.name,context))
        with template_rendered.connected_to(capture,module.app):
            self.assertEqual(self.client.get('/applications/1/form').status_code,200)
        ctx=next(c for n,c in captured if n=='application_form.html')
        self.assertNotIn('correct_answer',ctx['questions'][0]);self.assertNotIn('grading',ctx)
        self.assertEqual(self.post('/applications/1/form',{'action':'review','q_area':'Defesa'}).status_code,302)
        self.assertEqual(self.post('/applications/1/review').status_code,302)
        self.as_user(1);question['correct_answer']='Ataque'
        self.assertEqual(self.post('/admin/jobs/1/form',{'questions_json':json.dumps([question])}).status_code,302)
        captured=[]
        with template_rendered.connected_to(capture,module.app):self.assertEqual(self.client.get('/admin/applications/1').status_code,200)
        grading=next(c['grading'] for n,c in captured if n=='admin_application.html')
        self.assertEqual((grading['correct'],grading['total']),(1,1))
        self.assertEqual(grading['items'][0]['correct_answer'],'Defesa')
        self.assertEqual(self.rows('SELECT COUNT(*) FROM form_answer_keys'),[(2,)])
        self.assertEqual(self.rows('SELECT status FROM applications'),[('submitted',)])
        self.as_user(3)
        self.assertEqual(self.post('/applications/1/form',{'action':'review','q_area':'Defesa'}).status_code,302)
        self.assertEqual(self.post('/applications/1/review').status_code,302)
        self.as_user(1);captured=[]
        with template_rendered.connected_to(capture,module.app):self.assertEqual(self.client.get('/admin/applications/2').status_code,200)
        grading=next(c['grading'] for n,c in captured if n=='admin_application.html')
        self.assertEqual((grading['correct'],grading['total']),(0,1))
        self.assertEqual(self.rows('SELECT status FROM applications ORDER BY id'),[('submitted',),('submitted',)])

    def test_answer_key_requires_matching_single_choice_option(self):
        q=dict(id='q',label='Pergunta?',type='select',required=True,options=['Sim','Não'],correct_answer='Talvez')
        with self.assertRaises(ValueError):recruitment.validate_questions([q])
        q.update(type='multiselect',correct_answer='Sim')
        with self.assertRaises(ValueError):recruitment.validate_questions([q])

    def test_custom_form_choices_persist_and_are_visible_only_to_evaluator(self):
        questions=[dict(id='area',label='Qual área?',type='select',required=True,options=['Ataque','Defesa']),
                   dict(id='skills',label='Quais habilidades?',type='multiselect',required=True,options=['Logs','Web']),
                   dict(id='hours',label='Horas disponíveis?',type='number',required=True,options=[])]
        self.as_user(1)
        self.assertEqual(self.post('/admin/jobs/1/form',{'questions_json':json.dumps(questions)}).status_code,302)
        self.as_user(2)
        token=self.token()
        data=MultiDict([('csrf_token','test'),('form_token',token),('action','review'),('q_area','Defesa'),('q_skills','Logs'),('q_skills','Web'),('q_hours','12')])
        self.assertEqual(self.client.post('/applications/1/form',data=data).status_code,302)
        self.assertEqual(self.post('/applications/1/review').status_code,302)
        self.assertEqual(self.rows("SELECT value FROM application_answers ORDER BY question_id,position"),[('Defesa',),('Logs',),('Web',),('12',)])
        self.as_user(3)
        self.assertEqual(self.client.get('/admin/applications/1').status_code,403)
        self.as_user(1)
        response=self.client.get('/admin/applications/1')
        for value in (b'Defesa',b'Logs',b'Web',b'12'):self.assertIn(value,response.data)

    def test_custom_form_rejects_forged_choices_and_invalid_number(self):
        questions=[dict(id='area',label='Qual área?',type='select',required=True,options=['Defesa']),
                   dict(id='hours',label='Horas disponíveis?',type='number',required=True,options=[])]
        self.as_user(1);self.post('/admin/jobs/1/form',{'questions_json':json.dumps(questions)})
        self.as_user(2)
        for data in ({'q_area':'Forjada','q_hours':'12'}, {'q_area':'Defesa','q_hours':'inf'}):
            self.assertEqual(self.post('/applications/1/form',{'action':'review',**data}).status_code,400)
        self.assertEqual(self.rows('SELECT COUNT(*) FROM applications'),[(0,)])
    def test_safe_next_and_successful_login(self):
        for value in ['https://evil.test','//evil.test','/%5cevil.test','/x%0d%0aLocation:evil']:
            self.assertEqual(recruitment.safe_next(value),'')
        self.assertEqual(recruitment.safe_next('/applications/1/form'),'/applications/1/form')
        response=self.post('/login?next=/applications/1/form',{'email':'mentor@cti.local','password':'mentor123'})
        self.assertEqual(response.location,'/admin')
        self.post('/logout')
        self.write('UPDATE users SET password=? WHERE id=?',(generate_password_hash('candidate-password'),2))
        response=self.post('/login?next=/applications/1/form',{'email':'candidate@example.test','password':'candidate-password'})
        self.assertEqual(response.location,'/applications/1/form')
    def test_concurrent_confirmation_creates_one_history_event(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        self.draft()
        barrier=Barrier(2)
        def confirm():
            client=module.app.test_client()
            with client.session_transaction() as sess:sess.update(user_id=2,csrf='concurrent')
            page=client.get('/applications/1/review').get_data(as_text=True)
            token=unescape(re.search(r'name="confirmation_token" value="([^"]+)"',page).group(1))
            barrier.wait(timeout=5)
            return client.post('/applications/1/review',data={'csrf_token':'concurrent','confirmation_token':token}).status_code
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
