import hashlib
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from contextlib import closing
from flask import Flask

os.environ.setdefault('SECRET_KEY', 'challenge-editor-tests-only')
import app as module
import challenge_editor


class ChallengeEditorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous_db = module.DB
        module.DB = str(Path(self.temp.name) / 'editor.db')
        module.init_db()
        with closing(sqlite3.connect(module.DB)) as con, con:
            challenge_editor.migrate(con)
            con.execute("INSERT INTO users(id,name,email,role) VALUES(2,'Pessoa QA','person@qa.invalid','participante')")
        self.app = Flask(__name__, template_folder=str(Path(__file__).resolve().parents[1] / 'templates'))
        self.app.secret_key = 'challenge-editor-tests-only'
        self.app.config['TESTING'] = True
        self.app.before_request(module.protect_request)
        self.app.teardown_appcontext(module.close_db)
        self.app.jinja_env.globals['csrf_token'] = module.csrf_token
        challenge_editor.register_routes(self.app, module.db, module.mentor_required)
        self.client = self.app.test_client()
        module.RATE_BUCKETS.clear()
        self.as_user(1)

    def tearDown(self):
        module.DB = self.previous_db
        self.temp.cleanup()

    def as_user(self, uid):
        with self.client.session_transaction() as sess:
            sess.clear(); sess.update(user_id=uid, csrf='test')

    def post(self, route, data):
        return self.client.post(route, data={'csrf_token':'test', **data})

    def values(self, **changes):
        return dict(title='Desafio da equipe',category='Análise de logs',side='Blue Team',points='150',
            description='Analise os registros sintéticos e identifique o evento de interesse.',hint='Correlacione os horários.',
            state='published',answer='CTF{resposta_sintetica}',revision='1',**changes)

    def query(self, sql, args=()):
        with closing(sqlite3.connect(module.DB)) as con:
            return con.execute(sql,args).fetchall()

    def create(self):
        response=self.post('/admin/challenges/new',self.values())
        self.assertEqual(response.status_code,302)
        return self.query("SELECT id FROM challenges WHERE title='Desafio da equipe'")[0][0]

    def test_migration_is_incremental_idempotent_and_preserves_hashes(self):
        before=self.query('SELECT id,title,flag_hash FROM challenges')
        with closing(sqlite3.connect(module.DB)) as con,con:
            challenge_editor.migrate(con);challenge_editor.migrate(con)
        self.assertEqual(before,self.query('SELECT id,title,flag_hash FROM challenges'))
        self.assertEqual({r[0] for r in self.query('SELECT editorial_status FROM challenges')},{'published'})

    def test_create_edit_and_history_never_expose_answer(self):
        cid=self.create()
        expected=hashlib.sha256(b'CTF{resposta_sintetica}').hexdigest()
        self.assertEqual(self.query('SELECT flag_hash,editor_created FROM challenges WHERE id=?',(cid,)),[(expected,1)])
        for path in ['/admin/challenges',f'/admin/challenges/{cid}/edit']:
            response=self.client.get(path)
            self.assertEqual(response.status_code,200)
            self.assertNotIn(expected.encode(),response.data)
            self.assertNotIn(b'CTF{resposta_sintetica}',response.data)
        data=self.values();data.update(answer='',description='Briefing atualizado com contexto adicional para investigar os eventos.',state='paused')
        self.assertEqual(self.post(f'/admin/challenges/{cid}/edit',data).status_code,302)
        self.assertEqual(self.query('SELECT flag_hash,editorial_status,editorial_revision FROM challenges WHERE id=?',(cid,)),[(expected,'paused',2)])
        self.assertEqual(self.query('SELECT event FROM challenge_history WHERE challenge_id=? ORDER BY id',(cid,)),[('created',),('updated',)])

    def test_draft_requires_answer_before_publication(self):
        data=self.values();data.update(state='draft',answer='',description='')
        self.assertEqual(self.post('/admin/challenges/new',data).status_code,302)
        cid=self.query("SELECT id FROM challenges WHERE title='Desafio da equipe'")[0][0]
        data=self.values();data['answer']=''
        self.assertEqual(self.post(f'/admin/challenges/{cid}/edit',data).status_code,400)
        self.assertEqual(self.query('SELECT editorial_status FROM challenges WHERE id=?',(cid,)),[('draft',)])

    def test_attempts_freeze_response_points_and_side(self):
        cid=self.create()
        with closing(sqlite3.connect(module.DB)) as con,con:
            con.execute('INSERT INTO attempts(user_id,challenge_id,correct,created_at) VALUES(2,?,0,1)',(cid,))
        for changes in [{'points':'200'},{'side':'Red Team'},{'answer':'CTF{outra}'}]:
            data=self.values();data['answer']='';data.update(changes)
            self.assertEqual(self.post(f'/admin/challenges/{cid}/edit',data).status_code,400)
        data=self.values();data.update(answer='',description='Apenas correção editorial, mantendo a resposta e os critérios da atividade.')
        self.assertEqual(self.post(f'/admin/challenges/{cid}/edit',data).status_code,302)

    def test_conflict_preserves_input_and_does_not_overwrite(self):
        cid=self.create();data=self.values();data.update(answer='',description='Primeira correção salva pela equipe com contexto suficiente.')
        self.assertEqual(self.post(f'/admin/challenges/{cid}/edit',data).status_code,302)
        data['description']='Segunda edição que precisa ser preservada sem sobrescrever a versão atual.'
        response=self.post(f'/admin/challenges/{cid}/edit',data)
        self.assertEqual(response.status_code,409)
        self.assertIn(data['description'].encode(),response.data)
        self.assertEqual(self.query('SELECT description FROM challenges WHERE id=?',(cid,)),[('Primeira correção salva pela equipe com contexto suficiente.',)])

    def test_legacy_title_cannot_be_renamed_and_seed_remains_stable(self):
        row=self.query('SELECT id,title,category,side,points,description,hint FROM challenges WHERE image IS NULL LIMIT 1')[0]
        data=dict(zip(('id','title','category','side','points','description','hint'),row))
        cid=data.pop('id');data.update(title='Título alterado',state='published',revision='1',answer='')
        response=self.post(f'/admin/challenges/{cid}/edit',data)
        self.assertEqual(response.status_code,400)
        self.assertEqual(self.query('SELECT title FROM challenges WHERE id=?',(cid,)),[(row[1],)])

    def test_authorization_csrf_and_controlled_docker(self):
        self.as_user(2)
        self.assertEqual(self.client.get('/admin/challenges').status_code,403)
        self.assertEqual(self.post('/admin/challenges/new',self.values()).status_code,403)
        self.as_user(1)
        self.assertEqual(self.client.post('/admin/challenges/new',data=self.values()).status_code,400)
        cid=self.query('SELECT id FROM challenges WHERE image IS NOT NULL LIMIT 1')[0][0]
        response=self.client.get(f'/admin/challenges/{cid}/edit')
        self.assertEqual(response.status_code,200)
        self.assertNotIn(b'name="answer"',response.data)
        self.assertEqual(self.post(f'/admin/challenges/{cid}/edit',self.values()).status_code,403)

    def test_validation_preserves_escaped_content_without_reflecting_answer(self):
        data=self.values();data.update(title='<script>alert(1)</script>',points='-1',answer='CTF{never_echo_this}')
        response=self.post('/admin/challenges/new',data)
        self.assertEqual(response.status_code,400)
        self.assertIn(b'&lt;script&gt;',response.data)
        self.assertNotIn(b'<script>alert(1)</script>',response.data)
        self.assertNotIn(b'never_echo_this',response.data)
        data=self.values();data['image']='untrusted/image'
        self.assertEqual(self.post('/admin/challenges/new',data).status_code,400)


if __name__=='__main__':unittest.main()
