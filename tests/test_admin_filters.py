import os
import re
import sqlite3
import tempfile
import unittest
from contextlib import closing
from flask import template_rendered
import app as module


class AdminFilterTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.old=module.DB
        module.DB=os.path.join(self.temp.name,'admin.db');module.app.config['TESTING']=True
        module.RATE_BUCKETS.clear();module.init_db();self.client=module.app.test_client()
        with closing(sqlite3.connect(module.DB)) as con,con:
            for jid,title in [(1,'SOC'),(2,'AppSec')]:
                con.execute('INSERT INTO jobs(id,title,company,description,side,min_points,active) VALUES(?,?,?,? ,?,0,1)',(jid,title,'Equipe','Descrição da oportunidade','Blue Team'))
            for i in range(1,47):
                name='Rascunho privado' if i==46 else f'Pessoa {i:02}'
                con.execute('INSERT INTO users(id,name,email,role) VALUES(?,?,?,?)',(i+1,name,f'{i}@example.test','participante'))
                con.execute('INSERT INTO applications(id,job_id,user_id,status,created_at) VALUES(?,?,?,?,1)',(i,1 if i<=30 else 2,i+1,'draft' if i==46 else 'review' if i%2==0 else 'submitted'))
        with self.client.session_transaction() as s:s.update(user_id=1,csrf='token')
        self.context=None
        def receiver(sender,template,context,**kwargs):self.context=context
        self.receiver=receiver;template_rendered.connect(receiver,module.app,weak=False)

    def tearDown(self):
        template_rendered.disconnect(self.receiver,module.app);module.DB=self.old;self.temp.cleanup()

    def ids(self,response):return set(re.findall(rb'/admin/applications/(\d+)',response.data))

    def test_pages_are_bounded_disjoint_and_drafts_excluded(self):
        first=self.client.get('/admin');self.assertEqual(first.status_code,200)
        self.assertEqual(len(self.context['applications']),20)
        self.assertEqual(self.context['pagination']['total'],45)
        self.assertEqual(self.context['stats']['applications'],45)
        self.assertEqual(self.context['stats']['drafts'],1)
        second=self.client.get('/admin?page=2');third=self.client.get('/admin?page=3')
        self.assertEqual(len(self.ids(second)),20);self.assertEqual(len(self.ids(third)),5)
        self.assertFalse(self.ids(first)&self.ids(second))
        self.assertNotIn(b'Rascunho privado',first.data+second.data+third.data)

    def test_combined_filters_and_links_preserve_parameters(self):
        response=self.client.get('/admin?q=Pessoa&status=review&job_id=1')
        self.assertEqual(response.status_code,200)
        self.assertEqual(self.context['pagination']['total'],15)
        self.assertEqual(self.context['stats']['applications'],45)
        self.assertTrue(all(row['job_id']==1 and row['status']=='review' for row in self.context['applications']))
        response=self.client.get('/admin?q=Pessoa')
        self.assertIn(b'q=Pessoa',response.data);self.assertIn(b'page=2',response.data)
        self.client.get('/admin?q=AppSec');self.assertEqual(self.context['pagination']['total'],15)

    def test_literal_search_and_empty_result(self):
        response=self.client.get('/admin?q=%25')
        self.assertEqual(self.context['pagination']['total'],0)
        self.assertIn('Nenhuma candidatura corresponde'.encode(),response.data)
        self.client.get('/admin?q=Pessoa+01');self.assertEqual(self.context['pagination']['total'],1)

    def test_invalid_filters_are_controlled(self):
        for query in ['page=0','page=-1','page=abc','page=99999999999999999999','status=draft','status=unknown','job_id=0','job_id=x','job_id=999999999999999999999','q='+'x'*121]:
            with self.subTest(query=query):self.assertEqual(self.client.get('/admin?'+query).status_code,400)
        self.client.get('/admin?page=999');self.assertEqual(self.context['pagination']['page'],3)

    def test_participant_cannot_use_filters_to_access_admin(self):
        with self.client.session_transaction() as s:s['user_id']=2
        self.assertEqual(self.client.get('/admin?q=Pessoa&job_id=1').status_code,403)

if __name__=='__main__':unittest.main()
