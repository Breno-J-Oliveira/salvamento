import os
import re
import sqlite3
import tempfile
import time
import unittest
from contextlib import closing
from datetime import datetime,timezone
from unittest.mock import patch
import app as module
import vacancies

class VacancyTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.old=module.DB
        module.DB=os.path.join(self.temp.name,'vacancies.db');module.app.config['TESTING']=True
        module.RATE_BUCKETS.clear();module.init_db();self.client=module.app.test_client()
        self.renderer=patch('vacancies.render_template',return_value='editor');self.renderer.start()
        with self.connection() as con:
            con.execute("INSERT INTO users(id,name,email,role) VALUES(2,'Candidate','candidate@example.test','participante')")
        self.as_user(1)
    def tearDown(self):
        self.renderer.stop();module.DB=self.old;self.temp.cleanup()
    def connection(self):
        from contextlib import contextmanager
        @contextmanager
        def opened():
            con=sqlite3.connect(module.DB)
            try:
                with con:yield con
            finally:con.close()
        return opened()
    def rows(self,sql,args=()):
        with self.connection() as con:return con.execute(sql,args).fetchall()
    def as_user(self,uid):
        with self.client.session_transaction() as s:s.update(user_id=uid,csrf='token')
    def post(self,path,data=None):return self.client.post(path,data={'csrf_token':'token',**(data or {})})
    def data(self,**extra):
        return dict(title='Analista SOC',company='Empresa QA',description='Investigação de eventos e comunicação de incidentes.',side='Blue Team',min_points='0',seniority='Júnior',modality='Remoto',location='',deadline='',revision='1',action='publish',**extra)
    def create(self,action='publish'):
        data=self.data();data['action']=action
        self.assertEqual(self.post('/admin/jobs/new',data).status_code,302)
    def test_migration_maps_legacy_and_is_idempotent(self):
        with closing(sqlite3.connect(os.path.join(self.temp.name,'legacy.db'))) as con,con:
            con.execute('CREATE TABLE jobs(id INTEGER PRIMARY KEY,active INTEGER)')
            con.executemany('INSERT INTO jobs VALUES(?,?)',[(1,1),(2,0)])
            vacancies.migrate(con);vacancies.migrate(con)
            self.assertEqual(con.execute('SELECT status,revision FROM jobs ORDER BY id').fetchall(),[('published',1),('paused',1)])
    def test_create_draft_publish_and_history(self):
        values=self.data();values.update(action='save_draft',company='',description='')
        self.assertEqual(self.post('/admin/jobs/new',values).status_code,302)
        self.assertEqual(self.rows('SELECT status,active FROM jobs'),[('draft',0)])
        self.assertEqual(self.client.get('/opportunities/1').status_code,404)
        self.assertEqual(self.post('/admin/jobs/1/state',{'state':'published','revision':'1'}).status_code,400)
        values=self.data();self.assertEqual(self.post('/admin/jobs/1/edit',values).status_code,302)
        self.assertEqual(self.rows('SELECT status,active,revision FROM jobs'),[('published',1,2)])
        self.assertEqual(self.rows('SELECT COUNT(*) FROM job_history'),[(2,)])
    def test_states_idempotent_closed_cannot_reopen(self):
        self.create()
        for _ in range(2):self.assertEqual(self.post('/admin/jobs/1/state',{'state':'paused','revision':'1'}).status_code,302)
        self.assertEqual(self.rows('SELECT revision FROM jobs'),[(2,)])
        self.assertEqual(self.post('/admin/jobs/1/state',{'state':'closed','revision':'2'}).status_code,302)
        self.assertEqual(self.post('/jobs/1/toggle',{'active':'1'}).status_code,400)
        self.assertEqual(self.post('/admin/jobs/1/state',{'state':'published','revision':'3'}).status_code,400)
        self.assertEqual(self.rows('SELECT status,active FROM jobs'),[('closed',0)])
        self.assertEqual(self.client.get('/opportunities/1').status_code,200)
    def test_edit_conflict_does_not_overwrite(self):
        self.create();values=self.data();values['title']='Primeira edição'
        self.assertEqual(self.post('/admin/jobs/1/edit',values).status_code,302)
        values['title']='Edição desatualizada'
        self.assertEqual(self.post('/admin/jobs/1/edit',values).status_code,409)
        self.assertEqual(self.rows('SELECT title,revision FROM jobs'),[('Primeira edição',2)])
        self.assertEqual(self.post('/admin/jobs/1/state',{'state':'paused','revision':'1'}).status_code,409)
    def test_extreme_dates_rejected_and_supported_deadline_renders(self):
        for raw in ('0001-01-01','1900-01-01','9999-12-30'):
            values=self.data();values.update(action='save_draft',deadline=raw)
            self.assertEqual(self.post('/admin/jobs/new',values).status_code,400)
        self.assertEqual(self.rows('SELECT COUNT(*) FROM jobs'),[(0,)])
        values=self.data();values.update(action='save_draft',deadline='2099-12-31')
        self.assertEqual(self.post('/admin/jobs/new',values).status_code,302)
        self.assertEqual(self.client.get('/admin/jobs/1/edit').status_code,200)
        deadline=self.rows('SELECT deadline_at FROM jobs')[0][0]
        self.assertEqual(vacancies.deadline_value(deadline),'2099-12-31')

    def test_deadline_uses_end_of_day_brasilia(self):
        values=self.data();values['deadline']='2030-01-02'
        self.assertEqual(self.post('/admin/jobs/new',values).status_code,302)
        deadline=self.rows('SELECT deadline_at FROM jobs')[0][0]
        self.assertEqual(datetime.fromtimestamp(deadline,timezone.utc).isoformat(),'2030-01-03T03:00:00+00:00')
        self.assertTrue(vacancies.is_open(dict(active=1,status='published',deadline_at=deadline),deadline-1))
        self.assertFalse(vacancies.is_open(dict(active=1,status='published',deadline_at=deadline),deadline))
        self.assertEqual(vacancies.deadline_value(deadline),'2030-01-02')
    def test_past_deadline_and_validation(self):
        for field,value in [('deadline','2000-01-01'),('deadline','not-date'),('side','Admin'),('modality','Invalid'),('seniority','Invalid'),('location','x'*121),('title','x')]:
            values=self.data();values[field]=value
            self.assertEqual(self.post('/admin/jobs/new',values).status_code,400,field)
        self.assertEqual(self.rows('SELECT COUNT(*) FROM jobs'),[(0,)])
    def test_expired_job_blocks_form_confirmation_and_legacy(self):
        self.create();self.as_user(2)
        form=self.client.get('/applications/1/form').get_data(as_text=True)
        token=re.search('name="form_token" value="([^"]+)"',form).group(1)
        self.assertEqual(self.post('/applications/1/form',{'action':'review','form_token':token,'q_availability':'Integral','q_experience':'Projeto de investigação de logs'}).status_code,302)
        with self.connection() as con:con.execute('UPDATE jobs SET deadline_at=1 WHERE id=1')
        self.assertNotIn(b'Analista SOC',self.client.get('/opportunities').data)
        self.assertEqual(self.post('/applications/1/review').status_code,400)
        self.assertEqual(self.post('/jobs/1/apply').status_code,404)
        self.assertEqual(self.post('/applications/1/form',{'action':'save','form_token':token}).status_code,400)
        self.assertEqual(self.rows('SELECT status FROM applications'),[('draft',)])
    def test_closing_preserves_applications_and_assessment_access(self):
        self.create()
        with self.connection() as con:con.execute("INSERT INTO applications(job_id,user_id,created_at,status) VALUES(1,2,1,'submitted')")
        self.post('/admin/jobs/1/state',{'state':'closed','revision':'1'});self.as_user(2)
        self.assertEqual(self.client.get('/my-applications/1/assessment').status_code,200)
        self.assertEqual(self.rows('SELECT COUNT(*) FROM applications'),[(1,)])
    def test_side_frozen_after_any_application(self):
        self.create()
        with self.connection() as con:con.execute("INSERT INTO applications(job_id,user_id,status) VALUES(1,2,'draft')")
        values=self.data();values['side']='Red Team'
        self.assertEqual(self.post('/admin/jobs/1/edit',values).status_code,400)
        self.assertEqual(self.rows('SELECT side FROM jobs'),[('Blue Team',)])
    def test_draft_does_not_leak_through_legacy_or_application_route(self):
        self.create('save_draft');self.as_user(2)
        self.assertNotIn(b'Analista SOC',self.client.get('/jobs').data)
        self.assertEqual(self.client.get('/applications/1/form').status_code,404)
        self.assertEqual(self.client.get('/opportunities/1').status_code,404)
        self.assertEqual(self.post('/jobs/1/apply').status_code,404)
    def test_closed_edit_preserves_terminal_state(self):
        self.create();self.post('/admin/jobs/1/state',{'state':'closed','revision':'1'})
        values=self.data();values.update(action='save',revision='2',title='SOC encerrada corrigida')
        self.assertEqual(self.post('/admin/jobs/1/edit',values).status_code,302)
        self.assertEqual(self.rows('SELECT title,status,active FROM jobs'),[('SOC encerrada corrigida','closed',0)])
        values.update(action='publish',revision='3')
        self.assertEqual(self.post('/admin/jobs/1/edit',values).status_code,400)

    def test_authorization_and_preview(self):
        self.create();self.as_user(2)
        for path in ['/admin/jobs/new','/admin/jobs/1/edit','/admin/jobs/1/preview']:
            self.assertEqual(self.client.get(path).status_code,403)
        self.assertEqual(self.post('/admin/jobs/1/state',{'state':'closed','revision':'1'}).status_code,403)
        self.as_user(1);self.assertEqual(self.client.get('/admin/jobs/1/preview').status_code,200)

if __name__=='__main__':unittest.main()
