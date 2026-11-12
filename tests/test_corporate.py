"""Avaliações internas isoladas, snapshots e notas privadas."""
import os
import sqlite3
import tempfile
import time
import unittest
from contextlib import closing
os.environ.setdefault('SECRET_KEY','corporate-tests-only')
import app as module
import corporate


class CorporateTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.old=module.DB
        module.DB=os.path.join(self.temp.name,'corporate.db'); module.app.config['TESTING']=True
        module.init_db()
        with closing(sqlite3.connect(module.DB)) as con,con:
            corporate.migrate(con)
            for uid in [2,3]:
                con.execute("INSERT INTO users(id,name,email,role) VALUES(?,?,?,'participante')",(uid,'Pessoa '+str(uid),f'{uid}@example.invalid'))
        self.client=module.app.test_client(); module.RATE_BUCKETS.clear()
        self.as_user(1)

    def tearDown(self):
        module.DB=self.old; self.temp.cleanup()

    def as_user(self,uid):
        with self.client.session_transaction() as sess:
            sess.clear();sess.update(user_id=uid,csrf='test-csrf')

    def post(self,url,data=None):
        return self.client.post(url,data={'csrf_token':'test-csrf',**(data or {})})

    def values(self,**changes):
        return dict(title='Investigação de incidente interno',context='Contexto fictício de autenticação e exportação: correlacione os registros autorizados fornecidos.',question_0='Que evidências você relacionaria primeiro?',question_1='Como verificaria uma hipótese concorrente?',question_2='Que decisão proporcional você justificaria?',deadline='',**changes)

    def scalar(self,sql):
        with closing(sqlite3.connect(module.DB)) as con:return con.execute(sql).fetchone()[0]

    def prepare(self):
        self.assertEqual(self.post('/admin/assessments/new',self.values()).status_code,302)
        self.assertEqual(self.post('/admin/assessments/1/assign',{'user_id':'2'}).status_code,302)
        return self.scalar('SELECT id FROM corporate_assignments')

    def answers(self,aid,revision=1,action='submit'):
        with closing(sqlite3.connect(module.DB)) as con:
            ids=[row[0] for row in con.execute('SELECT id FROM corporate_assignment_questions WHERE assignment_id=?',(aid,))]
        return {'revision':str(revision),'action':action,**{f'answer_{qid}':'Análise sintética: correlacionaria os identificadores e validaria a hipótese antes da contenção.' for qid in ids}}

    def review(self,revision):
        return dict(revision=str(revision),investigation='3',evidence='4',decisions='3',communication='4',justification='JUSTIFICATIVA-PRIVADA: correlaciona as evidências com limites documentados.',notes='NOTA-PRIVADA: conteúdo interno.',feedback='Análise recebida. Explique como validaria a hipótese na conversa com a equipe.')

    def test_full_flow_private_review_and_no_training_score(self):
        aid=self.prepare();self.as_user(2)
        data=self.answers(aid,action='save')
        self.assertEqual(self.post(f'/my-assessments/{aid}',data).status_code,302)
        self.assertEqual(self.scalar('SELECT status FROM corporate_assignments'), 'draft')
        self.assertEqual(self.post(f'/my-assessments/{aid}',self.answers(aid,2)).status_code,302)
        self.as_user(1)
        self.assertEqual(self.post(f'/admin/assessments/assignments/{aid}',self.review(3)).status_code,302)
        self.as_user(2);page=self.client.get(f'/my-assessments/{aid}')
        self.assertEqual(page.status_code,200);self.assertIn(b'An',page.data)
        self.assertIn(b'Explique como validaria',page.data)
        self.assertNotIn(b'NOTA-PRIVADA',page.data);self.assertNotIn(b'JUSTIFICATIVA-PRIVADA',page.data)
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM attempts'),0)
        # Duplicate submit is idempotent, cannot overwrite a reviewed answer.
        self.assertEqual(self.post(f'/my-assessments/{aid}',self.answers(aid)).status_code,302)
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM corporate_reviews'),1)

    def test_ownership_roles_csrf_and_assignment_idempotency(self):
        aid=self.prepare()
        self.assertEqual(self.post('/admin/assessments/1/assign',{'user_id':'2'}).status_code,302)
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM corporate_assignments'),1)
        self.assertEqual(self.post('/admin/assessments/1/assign',{'user_id':'1'}).status_code,400)
        self.as_user(3)
        self.assertEqual(self.client.get(f'/my-assessments/{aid}').status_code,403)
        self.assertEqual(self.post(f'/my-assessments/{aid}',self.answers(aid)).status_code,403)
        self.assertEqual(self.client.get('/admin/assessments').status_code,403)
        self.assertEqual(self.post('/admin/assessments/new',self.values()).status_code,403)
        self.as_user(2)
        self.assertEqual(self.client.post(f'/my-assessments/{aid}',data=self.answers(aid)).status_code,400)

    def test_snapshots_preserved_and_editor_conflict(self):
        aid=self.prepare()
        changed=self.values();changed.update(title='Novo título da definição',context='Novo contexto sintético preservando avaliações anteriores.',question_0='Nova pergunta para futuras atribuições?',revision='1')
        self.assertEqual(self.post('/admin/assessments/1/edit',changed).status_code,302)
        self.assertEqual(self.scalar('SELECT template_revision FROM corporate_assignments'),1)
        self.assertEqual(self.scalar('SELECT title FROM corporate_assignments'),'Investigação de incidente interno')
        response=self.post('/admin/assessments/1/edit',changed)
        self.assertEqual(response.status_code,409);self.assertIn(b'Novo t',response.data)
        self.as_user(2);page=self.client.get(f'/my-assessments/{aid}')
        self.assertIn('Que evidências'.encode(),page.data);self.assertNotIn(b'Nova pergunta',page.data)

    def test_draft_review_conflicts_and_invalid_scores(self):
        aid=self.prepare();self.as_user(2)
        self.assertEqual(self.post(f'/my-assessments/{aid}',self.answers(aid,action='save')).status_code,302)
        self.assertEqual(self.post(f'/my-assessments/{aid}',self.answers(aid)).status_code,409)
        self.assertEqual(self.post(f'/my-assessments/{aid}',{'action':'submit','revision':'2'}).status_code,400)
        self.assertEqual(self.post(f'/my-assessments/{aid}',self.answers(aid,2)).status_code,302)
        self.as_user(1);bad=self.review(3);bad['evidence']='6'
        self.assertEqual(self.post(f'/admin/assessments/assignments/{aid}',bad).status_code,400)
        self.assertEqual(self.post(f'/admin/assessments/assignments/{aid}',self.review(3)).status_code,302)
        self.assertEqual(self.post(f'/admin/assessments/assignments/{aid}',self.review(3)).status_code,409)
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM corporate_reviews'),1)

    def test_deadline_blocks_new_assignment_and_submission_without_erasing(self):
        aid=self.prepare();self.as_user(2)
        self.post(f'/my-assessments/{aid}',self.answers(aid,action='save'))
        with closing(sqlite3.connect(module.DB)) as con,con:
            con.execute('UPDATE corporate_assignments SET deadline_at=?',(int(time.time())-1,))
            con.execute('UPDATE corporate_assessments SET deadline_at=?',(int(time.time())-1,))
        self.assertEqual(self.post(f'/my-assessments/{aid}',self.answers(aid,2)).status_code,400)
        self.assertTrue(self.scalar('SELECT length(answer) FROM corporate_assignment_questions LIMIT 1')>30)
        self.as_user(1)
        self.assertEqual(self.post('/admin/assessments/1/assign',{'user_id':'3'}).status_code,400)
        self.assertEqual(self.post(f'/admin/assessments/assignments/{aid}',self.review(2)).status_code,400)

    def test_oversized_revision_is_controlled_for_each_writer(self):
        aid=self.prepare()
        changes=self.values();changes['revision']='9'*5000
        self.assertEqual(self.post('/admin/assessments/1/edit',changes).status_code,409)
        self.as_user(2)
        self.assertEqual(self.post(f'/my-assessments/{aid}',self.answers(aid,revision='9'*5000)).status_code,409)
        self.assertEqual(self.post(f'/my-assessments/{aid}',self.answers(aid)).status_code,302)
        self.as_user(1)
        self.assertEqual(self.post(f'/admin/assessments/assignments/{aid}',self.review('9'*5000)).status_code,409)
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM corporate_reviews'),0)

    def test_editable_presets_and_unknown_scenario(self):
        for scenario in ['soc','access']:
            page=self.client.get('/admin/assessments/new?scenario='+scenario)
            self.assertEqual(page.status_code,200)
            self.assertIn('Cenário fictício'.encode(),page.data)
        self.assertEqual(self.client.get('/admin/assessments/new?scenario=unknown').status_code,400)
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM corporate_assessments'),0)

    def test_migration_repeat_and_portable_deadline(self):
        with closing(sqlite3.connect(module.DB)) as con,con:
            corporate.migrate(con);corporate.migrate(con)
            self.assertEqual(con.execute('PRAGMA foreign_key_check').fetchall(),[])
        self.assertIsNone(corporate.parse_deadline(''))
        self.assertEqual(corporate.parse_deadline('2026-11-19'),int(__import__('datetime').datetime(2026,11,20,tzinfo=corporate.BRASILIA).timestamp()))
        for value in ['9999-01-01','1900-01-01','not-date']:
            with self.assertRaises(ValueError):corporate.parse_deadline(value)

if __name__=='__main__':unittest.main()
