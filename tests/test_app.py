import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from contextlib import contextmanager
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-production-secret')
import app as module

class AppTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_db = module.DB
        module.DB = os.path.join(self.temp.name, 'test.db')
        module.app.config.update(TESTING=True)
        module.RATE_BUCKETS.clear()
        module.init_db()
        self.client = module.app.test_client()

    def tearDown(self):
        module.DB = self.old_db
        self.temp.cleanup()

    def post(self, path, data=None, client=None):
        client = client or self.client
        with client.session_transaction() as sess:
            sess['csrf'] = 'test-csrf'
        return client.post(path, data={'csrf_token':'test-csrf', **(data or {})})

    def register(self, email='person@example.com'):
        return self.post('/register', {'name':'Pessoa Teste', 'email':email, 'password':'safe-pass123', 'team':'Equipe'})

    def login(self, mentor=False):
        if not mentor:
            self.register()
        return self.post('/login', {'email':'mentor@cti.local' if mentor else 'person@example.com', 'password':'mentor123' if mentor else 'safe-pass123'})

    @contextmanager
    def connection(self):
        connection = sqlite3.connect(module.DB)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def scalar(self, sql):
        with self.connection() as con:
            return con.execute(sql).fetchone()[0]

    def test_anonymous_protected_pages(self):
        for path in ['/challenges','/challenge/1','/dashboard','/ranking','/profile','/jobs','/ambientes','/participante/1']:
            self.assertEqual(self.client.get(path).status_code,302,path)

    def test_csrf_rejected(self):
        self.assertEqual(self.client.post('/login',data={}).status_code,400)
        self.login()
        self.assertEqual(self.client.post('/challenge/1',data={'flag':'x'}).status_code,400)

    def test_register_valid_and_role_not_escalated(self):
        response=self.post('/register',{'name':'Pessoa Teste','email':'  PERSON@example.com  ','password':'long-password','role':'mentor'})
        self.assertEqual(response.status_code,302)
        self.assertEqual(self.scalar("SELECT role FROM users WHERE email='person@example.com'"),'participante')
        self.assertNotEqual(self.scalar("SELECT password FROM users WHERE email='person@example.com'"),'long-password')

    def test_register_validation(self):
        for changes in [{'name':''},{'email':'bad'},{'password':'x'},{'password':'x'*129},{'team':'x'*81}]:
            data={'name':'Pessoa','email':'new@example.com','password':'safe-pass123',**changes}
            self.assertEqual(self.post('/register',data).status_code,400)
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM users'),1)

    def test_duplicate_registration(self):
        self.register(); self.register()
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM users'),2)

    def test_login_invalid_and_logout(self):
        self.register()
        self.post('/login',{'email':"' OR 1=1 --",'password':'bad'})
        with self.client.session_transaction() as sess:self.assertNotIn('user_id',sess)
        self.login()
        self.assertEqual(self.client.get('/logout').status_code,405)
        self.assertEqual(self.post('/logout').status_code,302)
        self.assertEqual(self.client.get('/challenges').status_code,302)

    def test_participant_cannot_access_mentor(self):
        self.login()
        for path in ['/dashboard','/ambientes','/participante/1']:
            self.assertEqual(self.client.get(path).status_code,403)
        for path in ['/ambientes/1/encerrar','/ambientes/encerrar-todos','/jobs/1/toggle','/jobs']:
            self.assertEqual(self.post(path).status_code,403)

    def test_role_rechecked_from_database(self):
        self.login(mentor=True)
        with self.connection() as con:con.execute("UPDATE users SET role='participante' WHERE id=1")
        self.assertEqual(self.client.get('/dashboard').status_code,403)

    def test_correct_flag_scores_once(self):
        self.login()
        for _ in range(3):self.post('/challenge/1',{'flag':'CTF{bem_vindo_ao_purple_lab}'})
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM attempts WHERE correct=1'),1)
        with module.app.test_request_context():
            self.assertEqual(module.stats()[0]['points'],50)

    def test_invalid_flags_no_points(self):
        self.login()
        self.post('/challenge/1',{'flag':'wrong'})
        self.post('/challenge/1',{'flag':''})
        self.post('/challenge/1',{'flag':'x'*513})
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM attempts'),1)
        self.assertEqual(self.scalar('SELECT SUM(correct) FROM attempts'),0)

    def test_lab_requires_own_active_instance(self):
        self.login()
        self.post('/challenge/2',{'flag':'CTF{anything}'})
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM attempts'),0)
        with self.connection() as con:
            con.execute('INSERT INTO instances(user_id,challenge_id,flag_hash,active,expires_at) VALUES(?,?,?,?,?)',(1,2,module.h('CTF{other}'),1,9999999999))
        self.post('/challenge/2',{'flag':'CTF{other}'})
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM attempts'),0)

    def test_lab_unique_flag_and_expiry(self):
        self.login()
        with patch.object(module.orch,'start',return_value=12345):self.post('/challenge/2/start')
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM instances WHERE active=1'),1)
        with self.connection() as con:
            con.execute('UPDATE instances SET flag_hash=?',(module.h('CTF{mine}'),))
        self.post('/challenge/2',{'flag':'CTF{mine}'})
        self.assertEqual(self.scalar('SELECT SUM(correct) FROM attempts'),1)

    def test_start_idempotent_and_failure_not_leaked(self):
        self.login()
        with patch.object(module.orch,'start',return_value=12345) as start, patch.object(module.orch,'status',return_value=True):
            self.post('/challenge/2/start'); self.post('/challenge/2/start')
            self.assertEqual(start.call_count,1)
        with patch.object(module.orch,'stop',side_effect=module.orch.DockerError('secret sentinel')):
            self.post('/challenge/2/stop')
            self.assertEqual(self.scalar('SELECT active FROM instances'),1)
        with patch.object(module.orch,'stop',return_value=None):self.post('/challenge/2/stop')
        with patch.object(module.orch,'start',side_effect=module.orch.DockerError('secret sentinel')):
            self.post('/challenge/2/start')
        with self.client.session_transaction() as sess:self.assertNotIn('secret sentinel',str(sess.get('_flashes')))

    def test_reaper_preserves_failed_instances(self):
        with self.connection() as con:
            con.execute("INSERT INTO instances(container,active,expires_at) VALUES('lab-u1-c2-abcdef',1,0)")
        with patch.object(module.orch,'stop',side_effect=module.orch.DockerError('failure')):module.reap_expired()
        self.assertEqual(self.scalar('SELECT active FROM instances'),1)
        with patch.object(module.orch,'stop',return_value=None):module.reap_expired()
        self.assertEqual(self.scalar('SELECT active FROM instances'),0)

    def test_init_preserves_users_and_instances(self):
        self.register()
        with self.connection() as con:con.execute("INSERT INTO instances(active,expires_at) VALUES(1,9999999999)")
        module.init_db()
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM users'),2)
        self.assertEqual(self.scalar('SELECT active FROM instances'),1)

    def test_profile_validation_and_update(self):
        self.login()
        self.assertEqual(self.post('/profile',{'name':'','team':'A'}).status_code,400)
        self.post('/profile',{'name':'Nome Novo','team':'Equipe Nova','role':'mentor'})
        self.assertEqual(self.scalar('SELECT name FROM users WHERE id=2'),'Nome Novo')
        self.assertEqual(self.scalar('SELECT role FROM users WHERE id=2'),'participante')

    def test_evaluation_validation(self):
        self.register(); self.login(mentor=True)
        good={'logica':'5','comunicacao':'4','colaboracao':'3','decisao':'2','notes':'Avaliação técnica'}
        for value in ['abc','0','6','1.5']:
            self.assertEqual(self.post('/participante/2',{**good,'logica':value}).status_code,400)
        self.assertEqual(self.post('/participante/2',good).status_code,302)
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM evaluations'),1)
        self.assertEqual(self.post('/participante/1',good).status_code,404)

    def test_jobs_create_apply_duplicate_pause(self):
        self.login(mentor=True)
        good={'title':'Analista SOC','company':'Empresa','description':'Análise de incidentes de segurança','side':'Blue Team','min_points':'100'}
        self.assertEqual(self.post('/jobs',{**good,'min_points':'nan'}).status_code,400)
        self.assertEqual(self.post('/jobs',good).status_code,302)
        self.post('/logout'); self.login()
        self.post('/jobs/1/apply'); self.post('/jobs/1/apply')
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM applications'),1)
        self.post('/logout'); self.login(mentor=True); self.post('/jobs/1/toggle'); self.post('/logout'); self.login()
        self.assertEqual(self.post('/jobs/1/apply').status_code,404)

    def test_rate_limit(self):
        for _ in range(10):self.post('/login',{'email':'nobody@example.com','password':'x'})
        self.assertEqual(self.post('/login',{}).status_code,429)

    def test_security_headers_and_size(self):
        response=self.client.get('/login')
        self.assertEqual(response.headers['X-Frame-Options'],'DENY')
        self.assertEqual(response.headers['Cache-Control'],'no-store')
        self.assertEqual(self.client.post('/login',data={'blob':'x'*70000}).status_code,413)

    def test_csrf_incorrect(self):
        with self.client.session_transaction() as sess:sess['csrf']='real'
        self.assertEqual(self.client.post('/login',data={'csrf_token':'fake'}).status_code,400)

    def test_xss_escaped(self):
        self.login()
        self.post('/profile',{'name':'<script>alert(1)</script>','team':'Equipe'})
        response=self.client.get('/challenges')
        self.assertNotIn(b'<script>alert(1)</script>',response.data)
        self.assertIn(b'&lt;script&gt;',response.data)

    def test_cannot_stop_other_users_instance(self):
        self.login()
        with self.connection() as con:
            con.execute("INSERT INTO instances(user_id,challenge_id,container,active,expires_at) VALUES(1,2,'lab-u1-c2-abcdef',1,9999999999)")
        with patch.object(module.orch,'stop') as stop:self.post('/challenge/2/stop');stop.assert_not_called()
        self.assertEqual(self.scalar('SELECT active FROM instances'),1)

    def test_expired_flag_rejected(self):
        self.login()
        with self.connection() as con:
            con.execute('INSERT INTO instances(user_id,challenge_id,flag_hash,active,expires_at) VALUES(?,?,?,?,?)',(2,2,module.h('CTF{expired}'),1,0))
        self.post('/challenge/2',{'flag':'CTF{expired}'})
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM attempts'),0)

    def test_global_capacity_prevents_start(self):
        self.login()
        with self.connection() as con:
            for i in range(module.MAX_ACTIVE):con.execute('INSERT INTO instances(user_id,challenge_id,active,expires_at) VALUES(?,?,1,9999999999)',(100+i,2))
        with patch.object(module.orch,'start') as start:self.post('/challenge/2/start');start.assert_not_called()

    def test_all_participant_pages_render(self):
        self.login()
        for path in ['/challenges','/challenge/1','/challenge/2','/ranking','/jobs','/profile']:
            self.assertEqual(self.client.get(path).status_code,200,path)

    def test_all_mentor_pages_render(self):
        self.register();self.login(mentor=True)
        for path in ['/dashboard','/participante/2','/ambientes','/ranking','/jobs','/profile']:
            self.assertEqual(self.client.get(path).status_code,200,path)

    def test_challenge_reconciles_missing_container(self):
        self.login()
        with patch.object(module.orch,'start',return_value=12345):self.post('/challenge/2/start')
        with patch.object(module.orch,'status',return_value=False):
            self.assertEqual(self.client.get('/challenge/2').status_code,200)
        self.assertEqual(self.scalar('SELECT active FROM instances'),0)

    def test_challenge_keeps_state_when_docker_unavailable(self):
        self.login()
        with patch.object(module.orch,'start',return_value=12345):self.post('/challenge/2/start')
        with patch.object(module.orch,'status',side_effect=module.orch.DockerError('offline')):
            response=self.client.get('/challenge/2')
            self.assertEqual(response.status_code,200)
            self.assertIn('Não foi possível confirmar'.encode(),response.data)
            self.assertNotIn('Abrir laboratório'.encode(),response.data)
        self.assertEqual(self.scalar('SELECT active FROM instances'),1)

    def test_missing_challenge(self):
        self.login()
        self.assertEqual(self.client.get('/challenge/999').status_code,404)
        self.assertEqual(self.post('/challenge/999/start').status_code,404)

if __name__=='__main__':unittest.main(verbosity=2)
