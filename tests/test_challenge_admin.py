import hashlib
import os
import sqlite3
import tempfile
import unittest
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-production-secret')
import app as module
from catalog_corporate import CORPORATE_CATALOG, seed_corporate_catalog


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


class CorporateCatalogTests(unittest.TestCase):
    def test_titles_unique_and_answers_use_ctf_format(self):
        titles = [i['title'] for i in CORPORATE_CATALOG]
        self.assertEqual(len(titles), len(set(titles)))
        for item in CORPORATE_CATALOG:
            with self.subTest(title=item['title']):
                self.assertRegex(item['answer'], r'^CTF\{[^{}\s]+\}$')
                self.assertIn(item['audience'], ('Colaboradores', 'Todos'))
                self.assertGreater(item['points'], 0)
                self.assertIn('Envie CTF{', item['description'])

    def test_catalog_covers_several_non_technical_areas(self):
        categories = {i['category'] for i in CORPORATE_CATALOG}
        self.assertGreaterEqual(len(categories), 10)
        for area in ('Financeiro', 'Recursos humanos', 'Vendas e comercial', 'Atendimento ao cliente', 'Jurídico e compliance'):
            self.assertIn(area, categories)

    def test_numeric_answers_match_independent_calculation(self):
        by_title = {i['title']: i['answer'] for i in CORPORATE_CATALOG}
        self.assertEqual(by_title['Meta trimestral'], 'CTF{%d}' % round((31500 + 38200 + 41050) / 120000 * 100))
        # banco de horas em minutos: 9h30, 8h, 10h15, 7h45, 8h contra jornada de 8h
        saldo = (9 * 60 + 30 - 480) + (10 * 60 + 15 - 480) + (7 * 60 + 45 - 480)
        self.assertEqual(by_title['Banco de horas'], 'CTF{%dh%02d}' % divmod(saldo, 60))
        self.assertEqual(by_title['Ponto de reposição'], 'CTF{%d}' % (40 * 9 + 120))
        self.assertEqual(by_title['Taxa de refugo'], 'CTF{%s}' % str(round((75 - 15) / 2500 * 100, 1)).replace('.', ','))
        cac = 18000 / 240
        self.assertEqual(by_title['Custo de aquisição'], 'CTF{%d-%d}' % (cac, 150 * 6 / cac))
        # maior desconto inteiro que mantém margem >= 30% sobre o preço de venda
        best = max(d for d in range(0, 100) if (1000 * (1 - d / 100) - 600) / (1000 * (1 - d / 100)) >= 0.30)
        self.assertEqual(by_title['Desconto com margem'], 'CTF{%d}' % best)
        saldo, first = 50000, None
        for day, delta in ((3, -45000), (5, 30000), (10, -40000), (15, 20000), (20, -10000)):
            saldo += delta
            if saldo < 0 and first is None:
                first = (day, -saldo)
        self.assertEqual(by_title['Caixa no vermelho'], 'CTF{%d-%d}' % first)
        growth = {'Norte': 138 / 120, 'Sul': 224 / 200, 'Leste': 180 / 150, 'Oeste': 100 / 80}
        self.assertEqual(by_title['Crescimento por região'], 'CTF{%s}' % max(growth, key=growth.get))
        score = {'P1': 8 / 2, 'P2': 9 / 9, 'P3': 5 / 1, 'P4': 3 / 8}
        self.assertEqual(by_title['Priorização de projetos'], 'CTF{%s}' % max(score, key=score.get))
        # primeiro lote a vencer (FEFO): datas no formato dia/mês
        lots = {'A': (12, 20), 'B': (12, 15), 'C': (12, 10)}
        self.assertEqual(by_title['Primeiro a vencer, primeiro a sair'], 'CTF{%s}' % min(lots, key=lambda k: lots[k][::-1]))
        self.assertEqual(by_title['Conciliação bancária'], 'CTF{%s}' % ('%.2f' % (154.90 - 145.90)).replace('.', ','))

    def test_seed_is_idempotent_and_keeps_existing(self):
        con = sqlite3.connect(':memory:')
        con.execute('CREATE TABLE challenges(id INTEGER PRIMARY KEY,title TEXT,category TEXT,side TEXT,points INTEGER,description TEXT,hint TEXT,url TEXT,flag_hash TEXT,audience TEXT)')
        con.execute("INSERT INTO challenges(id,title,flag_hash) VALUES(7,'Meta trimestral','custom')")
        seed_corporate_catalog(con)
        seed_corporate_catalog(con)
        self.assertEqual(con.execute('SELECT COUNT(*) FROM challenges').fetchone()[0], len(CORPORATE_CATALOG))
        self.assertEqual(con.execute("SELECT id,flag_hash FROM challenges WHERE title='Meta trimestral'").fetchone(), (7, 'custom'))
        con.close()


class ChallengeAdminTests(unittest.TestCase):
    FORM = dict(title='Fechamento do caixa', category='Financeiro', side='Corporativo', audience='Colaboradores',
                points='120', description='Some as entradas e subtraia as saídas do dia. Envie CTF{valor}.',
                answer='CTF{350}', active='1')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_db = module.DB
        module.DB = os.path.join(self.temp.name, 'test.db')
        module.app.config.update(TESTING=True)
        module.RATE_BUCKETS.clear()
        module.init_db()

    def tearDown(self):
        module.DB = self.old_db
        self.temp.cleanup()

    def post(self, path, data=None, client=None):
        with client.session_transaction() as sess:
            sess['csrf'] = 'test-csrf'
        return client.post(path, data={'csrf_token': 'test-csrf', **(data or {})})

    def mentor(self):
        client = module.app.test_client()
        self.post('/login', {'email': 'mentor@cti.local', 'password': 'mentor123'}, client)
        return client

    def participant(self, email='ana@example.com'):
        client = module.app.test_client()
        self.post('/register', {'name': 'Ana Teste', 'email': email, 'password': 'safe-pass123', 'team': 'RH'}, client)
        self.post('/login', {'email': email, 'password': 'safe-pass123'}, client)
        return client

    def row(self, sql, *args):
        con = sqlite3.connect(module.DB)
        try:
            return con.execute(sql, args).fetchone()
        finally:
            con.close()

    def create(self, client=None, **over):
        client = client or self.mentor()
        data = {**self.FORM, **over}
        if not data.get('active'):
            data.pop('active', None)
        return self.post('/admin/challenges', data, client)

    def cid(self, title='Fechamento do caixa'):
        return self.row('SELECT id FROM challenges WHERE title=?', title)[0]

    def test_corporate_catalog_seeded_and_visible_to_participants(self):
        self.assertEqual(self.row("SELECT COUNT(*) FROM challenges WHERE side='Corporativo'")[0], len(CORPORATE_CATALOG))
        page = self.participant().get('/challenges')
        self.assertIn('Conciliação bancária'.encode(), page.data)
        self.assertIn(b'data-audience-filter', page.data)

    def test_init_db_twice_does_not_duplicate_or_lose_data(self):
        before = self.row('SELECT COUNT(*) FROM challenges')[0]
        module.init_db()
        self.assertEqual(self.row('SELECT COUNT(*) FROM challenges')[0], before)

    def test_admin_pages_require_mentor(self):
        anon = module.app.test_client()
        for path in ('/admin/challenges', '/admin/challenges/1'):
            self.assertEqual(anon.get(path).status_code, 302)
        person = self.participant()
        for path in ('/admin/challenges', '/admin/challenges/1'):
            self.assertEqual(person.get(path).status_code, 403)
        self.assertEqual(self.post('/admin/challenges', self.FORM, person).status_code, 403)
        self.assertEqual(self.post('/admin/challenges/1/toggle', {}, person).status_code, 403)
        self.assertEqual(self.post('/admin/challenges/1/delete', {}, person).status_code, 403)
        self.assertIsNone(self.row("SELECT 1 FROM challenges WHERE title='Fechamento do caixa'"))

    def test_create_requires_csrf(self):
        self.assertEqual(self.mentor().post('/admin/challenges', data=self.FORM).status_code, 400)

    def test_mentor_page_and_nav_link(self):
        page = self.mentor().get('/admin/challenges')
        self.assertEqual(page.status_code, 200)
        self.assertIn(b'Novo desafio', page.data)
        self.assertIn(b'Criar desafios', page.data)

    def test_create_challenge_stores_hash_only_and_participant_can_solve(self):
        self.assertEqual(self.create().status_code, 302)
        cid, flag_hash, created_by, audience = self.row("SELECT id,flag_hash,created_by,audience FROM challenges WHERE title='Fechamento do caixa'")
        self.assertEqual(flag_hash, sha('CTF{350}'))
        self.assertEqual(audience, 'Colaboradores')
        self.assertIsNotNone(created_by)
        person = self.participant()
        self.assertEqual(person.get(f'/challenge/{cid}').status_code, 200)
        self.post(f'/challenge/{cid}', {'flag': 'CTF{999}'}, person)
        self.assertEqual(self.row('SELECT COUNT(*) FROM attempts WHERE correct=1')[0], 0)
        self.post(f'/challenge/{cid}', {'flag': 'CTF{350}'}, person)
        self.assertEqual(self.row('SELECT COUNT(*) FROM attempts WHERE challenge_id=? AND correct=1', cid)[0], 1)

    def test_answer_never_rendered_back(self):
        self.create()
        cid = self.cid()
        mentor = self.mentor()
        for path in ('/admin/challenges', f'/admin/challenges/{cid}', f'/challenge/{cid}'):
            self.assertNotIn(b'CTF{350}', mentor.get(path).data, path)

    def test_validation_errors(self):
        bad = [dict(title='ab'), dict(category=''), dict(side='Hacker'), dict(audience='Ninguem'), dict(points='5'),
               dict(points='abc'), dict(points='5000'), dict(description='curto'), dict(answer=''), dict(answer='x' * 201)]
        before = self.row('SELECT COUNT(*) FROM challenges')[0]
        client = self.mentor()
        for over in bad:
            with self.subTest(over=over):
                self.assertEqual(self.create(client, **over).status_code, 400)
        self.assertEqual(self.row('SELECT COUNT(*) FROM challenges')[0], before)

    def test_duplicate_title_rejected_case_insensitive(self):
        client = self.mentor()
        self.create(client)
        self.assertEqual(self.create(client, title='FECHAMENTO DO CAIXA').status_code, 400)
        self.assertEqual(self.create(client, title='Conciliação bancária').status_code, 400)

    def test_inactive_challenge_hidden_from_participants_only(self):
        mentor = self.mentor()
        self.create(mentor, active='')
        cid = self.cid()
        self.assertEqual(self.row('SELECT active FROM challenges WHERE id=?', cid)[0], 0)
        person = self.participant()
        self.assertNotIn(b'Fechamento do caixa', person.get('/challenges').data)
        self.assertEqual(person.get(f'/challenge/{cid}').status_code, 404)
        self.assertEqual(self.post(f'/challenge/{cid}', {'flag': 'CTF{350}'}, person).status_code, 404)
        self.assertIn(b'Fechamento do caixa', mentor.get('/challenges').data)
        self.assertEqual(mentor.get(f'/challenge/{cid}').status_code, 200)
        self.post(f'/admin/challenges/{cid}/toggle', {}, mentor)
        self.assertIn(b'Fechamento do caixa', person.get('/challenges').data)

    def test_edit_keeps_answer_when_blank_and_replaces_when_given(self):
        mentor = self.mentor()
        self.create(mentor)
        cid = self.cid()
        self.post(f'/admin/challenges/{cid}', {**self.FORM, 'title': 'Caixa do dia', 'points': '200', 'answer': ''}, mentor)
        self.assertEqual(self.row('SELECT title,points,flag_hash FROM challenges WHERE id=?', cid), ('Caixa do dia', 200, sha('CTF{350}')))
        self.post(f'/admin/challenges/{cid}', {**self.FORM, 'title': 'Caixa do dia', 'answer': 'CTF{400}'}, mentor)
        self.assertEqual(self.row('SELECT flag_hash FROM challenges WHERE id=?', cid)[0], sha('CTF{400}'))

    def test_edit_invalid_keeps_record_and_missing_returns_404(self):
        mentor = self.mentor()
        self.create(mentor)
        cid = self.cid()
        self.assertEqual(self.post(f'/admin/challenges/{cid}', {**self.FORM, 'points': '1'}, mentor).status_code, 400)
        self.assertEqual(self.row('SELECT points FROM challenges WHERE id=?', cid)[0], 120)
        self.assertEqual(mentor.get('/admin/challenges/99999').status_code, 404)
        self.assertEqual(self.post('/admin/challenges/99999/toggle', {}, mentor).status_code, 404)
        self.assertEqual(self.post('/admin/challenges/99999/delete', {}, mentor).status_code, 404)

    def test_delete_rules(self):
        mentor = self.mentor()
        self.create(mentor)
        cid = self.cid()
        # desafios do catálogo não são excluídos (seriam recriados na inicialização)
        catalog_id = self.cid('Meta trimestral')
        self.post(f'/admin/challenges/{catalog_id}/delete', {}, mentor)
        self.assertIsNotNone(self.row('SELECT 1 FROM challenges WHERE id=?', catalog_id))
        # com tentativas, preserva histórico e ranking
        person = self.participant()
        self.post(f'/challenge/{cid}', {'flag': 'CTF{350}'}, person)
        self.post(f'/admin/challenges/{cid}/delete', {}, mentor)
        self.assertIsNotNone(self.row('SELECT 1 FROM challenges WHERE id=?', cid))
        # sem tentativas, exclui
        self.create(mentor, title='Rascunho sem uso')
        other = self.cid('Rascunho sem uso')
        self.post(f'/admin/challenges/{other}/delete', {}, mentor)
        self.assertIsNone(self.row('SELECT 1 FROM challenges WHERE id=?', other))

    def test_lab_challenge_flag_not_editable(self):
        lab_id, original = self.row("SELECT id,flag_hash FROM challenges WHERE image='cti-lab/web-01'")
        mentor = self.mentor()
        self.assertNotIn(b'name="answer"', mentor.get(f'/admin/challenges/{lab_id}').data)
        self.post(f'/admin/challenges/{lab_id}', {**self.FORM, 'title': 'Intranet esquecida', 'answer': 'CTF{hack}'}, mentor)
        self.assertEqual(self.row('SELECT flag_hash FROM challenges WHERE id=?', lab_id)[0], original)

    def test_xss_in_challenge_fields_escaped(self):
        self.create(title='<script>alert(1)</script>', category='<b>x</b>y',
                    description='<img src=x onerror=alert(1)> cenário completo aqui')
        for client in (self.mentor(), self.participant()):
            for path in ('/challenges', '/admin/challenges'):
                data = client.get(path).data
                self.assertNotIn(b'<script>alert(1)</script>', data)
                self.assertNotIn(b'<img src=x', data)

    def test_inactive_excluded_from_totals_and_pages_still_render(self):
        before = self.row('SELECT COUNT(*) FROM challenges WHERE active=1')[0]
        mentor = self.mentor()
        self.create(mentor, active='')
        self.assertEqual(self.row('SELECT COUNT(*) FROM challenges WHERE active=1')[0], before)
        self.assertEqual(mentor.get('/ranking').status_code, 200)
        self.assertEqual(mentor.get('/dashboard').status_code, 200)
        self.assertEqual(mentor.get('/').status_code, 200)
        self.assertEqual(self.participant().get('/progress').status_code, 200)


if __name__ == '__main__':
    unittest.main()
