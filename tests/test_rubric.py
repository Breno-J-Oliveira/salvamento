import os
import sqlite3
import tempfile
import unittest
import app as module
import rubric


class RubricTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_db = module.DB
        module.DB = os.path.join(self.temp.name, 'rubric.db')
        module.app.config['TESTING'] = True
        module.RATE_BUCKETS.clear()
        module.init_db()
        con = sqlite3.connect(module.DB)
        try:
            con.execute("INSERT INTO users(id,name,email,role) VALUES(2,'Pessoa','candidate@example.test','participante')")
            con.execute("INSERT INTO jobs(id,title,company,description,side,min_points,active) VALUES(1,'SOC','Demo','Oportunidade sintética','Blue Team',0,1)")
            con.execute("INSERT INTO applications(id,job_id,user_id,status,created_at) VALUES(1,1,2,'review',1)")
            con.execute('INSERT INTO selection_assessments(application_id,started_at,updated_at,submitted_at) VALUES(1,1,1,1)')
            con.commit()
        finally:
            con.close()
        self.client = module.app.test_client()
        self.as_user(1)

    def tearDown(self):
        module.DB = self.old_db
        self.temp.cleanup()

    def as_user(self, uid):
        with self.client.session_transaction() as s:
            s.clear(); s.update(user_id=uid, csrf='token')

    def post(self, **changes):
        data = dict(csrf_token='token',revision='0',investigation='0',evidence='5',decisions='3',communication='4',
                    justification='Parecer interno baseado nas evidências apresentadas na avaliação seletiva.')
        return self.client.post('/admin/applications/1/rubric', data={**data, **changes})

    def execute(self, sql, parameters=()):
        con = sqlite3.connect(module.DB)
        try:
            result = con.execute(sql, parameters)
            rows = result.fetchall(); con.commit()
            return rows
        finally:
            con.close()

    def test_permissions_and_csrf(self):
        self.assertEqual(self.client.post('/admin/applications/1/rubric',data={}).status_code,400)
        self.as_user(2)
        self.assertEqual(self.post().status_code,403)
        anonymous = module.app.test_client()
        with anonymous.session_transaction() as s: s['csrf']='token'
        self.assertEqual(anonymous.post('/admin/applications/1/rubric',data={'csrf_token':'token'}).status_code,302)
        self.assertEqual(self.execute('SELECT COUNT(*) FROM selection_reviews')[0][0],0)

    def test_validation_preserves_fields(self):
        for changes in ({'investigation':'abc'},{'evidence':'6'},{'decisions':'-1'},{'communication':'2.5'},
                        {'revision':'-1'},{'revision':'x'},{'justification':'curto'},{'justification':'x'*4001}):
            with self.subTest(changes=changes):
                response = self.post(**changes)
                self.assertEqual(response.status_code,400)
                if 'justification' not in changes:
                    self.assertIn(b'Parecer interno',response.data)
        self.assertEqual(self.execute('SELECT COUNT(*) FROM selection_reviews')[0][0],0)

    def test_completed_assessment_required_and_drafts_hidden(self):
        self.execute('UPDATE selection_assessments SET submitted_at=NULL')
        self.assertEqual(self.post().status_code,400)
        self.execute("UPDATE applications SET status='draft'")
        self.assertEqual(self.post().status_code,404)
        self.execute('DELETE FROM applications')
        self.assertEqual(self.post().status_code,404)

    def test_append_only_history_and_optimistic_revision(self):
        self.assertEqual(self.post().status_code,302)
        response = self.post(justification='Outro parecer interno concorrente que não pode apagar a revisão anterior.')
        self.assertEqual(response.status_code,409)
        self.assertIn(b'Outro parecer interno concorrente',response.data)
        self.assertEqual(self.post(revision='1',investigation='5').status_code,302)
        self.assertEqual(self.execute('SELECT revision,reviewer_id,investigation,evidence,rubric_version FROM selection_reviews ORDER BY revision'),
                         [(1,1,0,5,1),(2,1,5,5,1)])
        self.assertEqual(self.execute('SELECT status,feedback,notes FROM applications WHERE id=1'), [('review','','')])
        self.assertEqual(self.execute('SELECT COUNT(*) FROM attempts')[0][0],0)
        with module.app.test_request_context():
            from flask import session
            session['role']='mentor'
            context={}; module.app.update_template_context(context)
            review=context['selection_rubric'](1)
            self.assertEqual(review['latest']['revision'],2)
            self.assertTrue(review['latest']['reviewed_at'].endswith('UTC'))
            self.assertEqual(review['latest']['reviewer_id'],1)

    def test_notes_remain_internal(self):
        self.assertEqual(self.post().status_code,302)
        self.as_user(2)
        self.assertNotIn(b'Parecer interno',self.client.get('/my-applications').data)
        with module.app.test_request_context():
            from flask import session
            session['role']='participante'
            context={}
            module.app.update_template_context(context)
            self.assertIsNone(context['selection_rubric'](1))

    def test_migration_is_repeatable(self):
        self.post()
        con=sqlite3.connect(module.DB)
        try: rubric.migrate(con);rubric.migrate(con)
        finally:con.close()
        self.assertEqual(self.execute('SELECT COUNT(*) FROM selection_reviews')[0][0],1)

    def test_database_enforces_score_and_revision_constraints(self):
        con=sqlite3.connect(module.DB)
        try:
            values=(1,1,1,6,2,3,4,'Justificativa suficientemente extensa para validar o limite.',1)
            with self.assertRaises(sqlite3.IntegrityError):
                con.execute('''INSERT INTO selection_reviews(application_id,revision,reviewer_id,
                    investigation,evidence,decisions,communication,justification,created_at)
                    VALUES(?,?,?,?,?,?,?,?,?)''',values)
            con.rollback()
        finally:con.close()
        self.assertEqual(self.post().status_code,302)
        con=sqlite3.connect(module.DB)
        try:
            with self.assertRaises(sqlite3.IntegrityError):
                con.execute('''INSERT INTO selection_reviews(application_id,revision,reviewer_id,
                    investigation,evidence,decisions,communication,justification,created_at)
                    SELECT application_id,revision,reviewer_id,investigation,evidence,decisions,
                    communication,justification,created_at FROM selection_reviews''')
            con.rollback()
        finally:con.close()


if __name__=='__main__':unittest.main()
