"""Presentation entry points keep public jobs and review queues truthful."""
import os
import sqlite3
import tempfile
import time
import unittest
from contextlib import closing

from flask import template_rendered
from werkzeug.security import generate_password_hash

os.environ.setdefault('SECRET_KEY', 'presentation-test-only')
import app as module


class PresentationFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous_db = module.DB
        module.DB = os.path.join(self.temp.name, 'presentation.db')
        module.app.config['TESTING'] = True
        module.RATE_BUCKETS.clear()
        module.init_db()
        self.client = module.app.test_client()
        self.context = None
        self.receiver = lambda sender, template, context, **kw: setattr(self, 'context', context)
        template_rendered.connect(self.receiver, module.app, weak=False)
        with closing(sqlite3.connect(module.DB)) as con, con:
            con.execute("INSERT INTO users(id,name,email,password,role) VALUES(2,'Pessoa','person@example.test',?,'participante')", (generate_password_hash('presentation-password'),))
            for jid, status, active, deadline in [(1,'draft',1,None),(2,'paused',0,None),(3,'closed',0,None),(4,'published',1,1),(5,'published',0,None),(6,'published',1,None),(7,'published',1,int(time.time())+86400),(8,'published',1,None),(9,'published',1,None)]:
                con.execute('INSERT INTO jobs(id,title,company,description,side,min_points,status,active,deadline_at,created_at) VALUES(?,?,?,?,?,0,?,?,?,?)', (jid, f'Vaga {jid}', 'Equipe fictícia', 'Descrição para demonstração', 'Blue Team', status, active, deadline, jid))

    def tearDown(self):
        template_rendered.disconnect(self.receiver, module.app)
        module.DB = self.previous_db
        self.temp.cleanup()

    def as_user(self, uid):
        with self.client.session_transaction() as sess:
            sess.clear()
            sess.update(user_id=uid, csrf='test')

    def test_featured_jobs_are_public_open_and_bounded(self):
        self.assertEqual(self.client.get('/').status_code, 200)
        self.assertEqual([row['id'] for row in self.context['featured_jobs']], [9,8,7])
        with closing(sqlite3.connect(module.DB)) as con, con:
            con.execute("UPDATE jobs SET status='closed'")
        self.assertEqual(self.client.get('/').status_code, 200)
        self.assertEqual(self.context['featured_jobs'], [])

    def test_participant_login_uses_context_or_applications(self):
        for target, expected in [('', '/my-applications'), ('/applications/6/form','/applications/6/form'), ('https://evil.example','/my-applications')]:
            with self.client.session_transaction() as sess:
                sess.clear()
                sess['csrf'] = 'test'
            response = self.client.post('/login', data={'csrf_token':'test','email':'person@example.test','password':'presentation-password','next':target})
            self.assertEqual(response.location, expected)

    def test_public_preparation_counts_current_questions_without_creating_forms(self):
        self.assertEqual(self.client.get('/opportunities/6').status_code, 200)
        self.assertEqual(self.context['question_count'], 3)
        with closing(sqlite3.connect(module.DB)) as con, con:
            self.assertEqual(con.execute('SELECT COUNT(*) FROM job_form_versions').fetchone()[0], 0)
            import recruitment
            questions = recruitment.defaults('Blue Team')[:1]
            version = recruitment.create_version(con, 6, questions, 1)
            con.execute('UPDATE jobs SET current_form_version=? WHERE id=6', (version,))
        response = self.client.get('/opportunities/6')
        self.assertEqual(self.context['question_count'], 1)
        self.assertIn(b'1 pergunta.', response.data)
        self.assertNotIn(b'Gabarito:', response.data)

    def test_work_queues_exclude_drafts_terminal_and_reviewed(self):
        with closing(sqlite3.connect(module.DB)) as con, con:
            for aid, status, delivered, reviewed in [(1,'review',True,False),(2,'submitted',False,False),(3,'draft',True,False),(4,'withdrawn',True,False),(5,'review',True,True),(6,'interview',True,False)]:
                uid = aid + 2
                con.execute('INSERT INTO users(id,name,email,role) VALUES(?,?,?,?)', (uid, f'Candidate {aid}', f'candidate{aid}@example.test', 'participante'))
                con.execute('INSERT INTO applications(id,job_id,user_id,status,created_at) VALUES(?,6,?,?,1)', (aid, uid, status))
                con.execute('INSERT INTO selection_assessments(application_id,started_at,updated_at,submitted_at) VALUES(?,1,1,?)', (aid, 2 if delivered else None))
                if reviewed:
                    con.execute('INSERT INTO selection_reviews(application_id,revision,reviewer_id,investigation,evidence,decisions,communication,justification,created_at) VALUES(?,1,1,3,3,3,3,?,3)', (aid,'Justificativa sintética com tamanho suficiente.'))
        self.as_user(1)
        self.assertEqual(self.client.get('/admin?work=ready').status_code, 200)
        self.assertEqual([a['id'] for a in self.context['applications']], [1])
        self.assertEqual(self.context['stats']['ready'], 1)
        self.assertEqual(self.context['stats']['ongoing'], 1)
        self.assertEqual(self.client.get('/admin?work=ongoing&job_id=6&status=submitted').status_code, 200)
        self.assertEqual([a['id'] for a in self.context['applications']], [2])
        self.assertEqual(self.client.get('/admin?work=unknown').status_code, 400)
        self.as_user(2)
        self.assertEqual(self.client.get('/admin?work=ready').status_code, 403)

    def test_candidate_assessment_flags_are_owned_and_do_not_load_notes(self):
        with closing(sqlite3.connect(module.DB)) as con, con:
            con.execute("INSERT INTO applications(id,job_id,user_id,status,created_at,notes) VALUES(1,6,2,'review',1,'PRIVATE-NOTE')")
            con.execute('INSERT INTO selection_assessments VALUES(1,1,1,2)')
        self.as_user(2)
        response = self.client.get('/my-applications')
        self.assertEqual(response.status_code, 200)
        own = self.context['applications'][0]
        self.assertTrue(own['assessment_submitted'])
        self.assertTrue(own['assessment_started'])
        self.assertNotIn('notes', own)
        self.assertNotIn(b'PRIVATE-NOTE', response.data)

    def test_work_filter_pagination_preserves_queue_and_global_counts(self):
        with closing(sqlite3.connect(module.DB)) as con, con:
            for number in range(21):
                uid = number + 3
                con.execute('INSERT INTO users(id,name,email,role) VALUES(?,?,?,?)', (uid, f'Pessoa {number}', f'page{number}@example.test', 'participante'))
                con.execute("INSERT INTO applications(job_id,user_id,status,created_at) VALUES(6,?,'submitted',1)", (uid,))
        self.as_user(1)
        first = self.client.get('/admin?work=ongoing&job_id=6')
        first_ids = {row['id'] for row in self.context['applications']}
        self.assertEqual(len(first_ids), 20)
        self.assertIn(b'work=ongoing', first.data)
        self.assertIn(b'page=2', first.data)
        self.client.get('/admin?work=ongoing&job_id=6&page=2')
        self.assertEqual(len(self.context['applications']), 1)
        self.assertNotIn(self.context['applications'][0]['id'], first_ids)
        self.assertEqual(self.context['stats']['ongoing'], 21)
        self.assertEqual(self.context['pagination']['total'], 21)


if __name__ == '__main__':
    unittest.main()
