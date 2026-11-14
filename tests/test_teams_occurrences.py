import os
import sqlite3
import tempfile
import threading
import unittest
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-production-secret')
import app as module
import occurrences
import teams


class Base(unittest.TestCase):
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

    def person(self, n):
        client = module.app.test_client()
        email = f'pessoa{n}@example.com'
        self.post('/register', {'name': f'Pessoa {n}', 'email': email, 'password': 'safe-pass123', 'team': 'Sem equipe'}, client)
        self.post('/login', {'email': email, 'password': 'safe-pass123'}, client)
        return client

    def row(self, sql, *args):
        con = sqlite3.connect(module.DB)
        try:
            return con.execute(sql, args).fetchone()
        finally:
            con.close()

    def uid(self, n):
        return self.row('SELECT id FROM users WHERE email=?', f'pessoa{n}@example.com')[0]

    def team_id(self, name):
        return self.row('SELECT id FROM teams WHERE name=?', name)[0]


class TeamTests(Base):
    def test_pages_require_login(self):
        anon = module.app.test_client()
        self.assertEqual(anon.get('/teams').status_code, 302)
        self.assertEqual(anon.post('/teams/create', data={'name': 'Time', 'side': 'Red Team'}).status_code, 400)
        self.assertEqual(self.row('SELECT COUNT(*) FROM teams')[0], 4)

    def test_create_team_and_membership(self):
        ana = self.person(1)
        self.assertEqual(self.post('/teams/create', {'name': 'Lobos do SOC', 'side': 'Blue Team'}, ana).status_code, 302)
        tid = self.team_id('Lobos do SOC')
        self.assertEqual(self.row('SELECT side FROM teams WHERE id=?', tid)[0], 'Blue Team')
        self.assertEqual(self.row('SELECT COUNT(*) FROM team_members WHERE team_id=?', tid)[0], 1)
        self.assertEqual(self.row("SELECT team FROM users WHERE email='pessoa1@example.com'")[0], 'Lobos do SOC')
        page = ana.get('/teams')
        self.assertEqual(page.status_code, 200)
        self.assertIn(b'Lobos do SOC', page.data)
        self.assertIn('Sair da equipe'.encode(), page.data)

    def test_validation_and_unique_name(self):
        ana, bia = self.person(1), self.person(2)
        for data in ({'name': 'ab', 'side': 'Red Team'}, {'name': 'Time bom', 'side': 'Green Team'}, {'name': 'x' * 41, 'side': 'Red Team'}, {'name': '   ', 'side': 'Red Team'}):
            self.post('/teams/create', data, ana)
        self.assertEqual(self.row('SELECT COUNT(*) FROM teams')[0], 4)
        self.post('/teams/create', {'name': 'Alfa', 'side': 'Red Team'}, ana)
        self.post('/teams/create', {'name': 'ALFA', 'side': 'Blue Team'}, bia)
        self.assertEqual(self.row('SELECT COUNT(*) FROM teams')[0], 5)

    def test_max_four_members_per_team(self):
        owner = self.person(1)
        self.post('/teams/create', {'name': 'Quatro', 'side': 'Red Team'}, owner)
        tid = self.team_id('Quatro')
        clients = [self.person(n) for n in range(2, 7)]
        for client in clients:
            self.post(f'/teams/{tid}/join', {}, client)
        self.assertEqual(self.row('SELECT COUNT(*) FROM team_members WHERE team_id=?', tid)[0], 4)
        # as duas últimas pessoas ficam sem equipe
        self.assertEqual(self.row('SELECT COUNT(*) FROM team_members')[0], 4)
        self.assertEqual(self.row("SELECT team FROM users WHERE email='pessoa6@example.com'")[0], 'Sem equipe')
        self.assertIn('Equipe completa'.encode(), clients[0].get('/teams').data)

    def test_concurrent_joins_never_exceed_limit(self):
        owner = self.person(1)
        self.post('/teams/create', {'name': 'Corrida', 'side': 'Blue Team'}, owner)
        tid = self.team_id('Corrida')
        clients = [self.person(n) for n in range(2, 10)]
        threads = [threading.Thread(target=self.post, args=(f'/teams/{tid}/join', {}, c)) for c in clients]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(self.row('SELECT COUNT(*) FROM team_members WHERE team_id=?', tid)[0], teams.MAX_MEMBERS)

    def test_one_team_per_person(self):
        ana = self.person(1)
        self.post('/teams/create', {'name': 'Time Um', 'side': 'Red Team'}, ana)
        self.post('/teams/create', {'name': 'Time Dois', 'side': 'Blue Team'}, ana)
        self.assertIsNone(self.row("SELECT 1 FROM teams WHERE name='Time Dois'"))
        bia = self.person(2)
        self.post('/teams/create', {'name': 'Outro time', 'side': 'Blue Team'}, bia)
        self.post(f'/teams/{self.team_id("Time Um")}/join', {}, bia)
        self.assertEqual(self.row('SELECT COUNT(*) FROM team_members WHERE user_id=?', self.uid(2))[0], 1)
        self.assertEqual(self.row('SELECT COUNT(*) FROM team_members')[0], 2)

    def test_leave_resets_label_and_empty_team_is_removed(self):
        ana, bia = self.person(1), self.person(2)
        self.post('/teams/create', {'name': 'Saida', 'side': 'Red Team'}, ana)
        self.post(f'/teams/{self.team_id("Saida")}/join', {}, bia)
        self.post('/teams/leave', {}, ana)
        self.assertEqual(self.row("SELECT team FROM users WHERE email='pessoa1@example.com'")[0], 'Sem equipe')
        self.assertIsNotNone(self.row("SELECT 1 FROM teams WHERE name='Saida'"))
        self.post('/teams/leave', {}, bia)
        self.assertIsNone(self.row("SELECT 1 FROM teams WHERE name='Saida'"))

    def test_mentor_cannot_join_but_can_manage(self):
        ana, mentor = self.person(1), self.mentor()
        self.post('/teams/create', {'name': 'Gestao', 'side': 'Blue Team'}, ana)
        tid = self.team_id('Gestao')
        self.assertEqual(self.post(f'/teams/{tid}/join', {}, mentor).status_code, 403)
        self.assertEqual(self.post('/teams/create', {'name': 'Mentor', 'side': 'Red Team'}, mentor).status_code, 403)
        bia = self.person(2)
        self.post(f'/teams/{tid}/join', {}, bia)
        bia_id = self.row("SELECT id FROM users WHERE email='pessoa2@example.com'")[0]
        self.assertEqual(self.post(f'/teams/{tid}/remove/{bia_id}', {}, ana).status_code, 403)
        self.post(f'/teams/{tid}/remove/{bia_id}', {}, mentor)
        self.assertEqual(self.row('SELECT COUNT(*) FROM team_members WHERE team_id=?', tid)[0], 1)
        self.assertIn(b'Desfazer equipe', mentor.get('/teams').data)
        self.assertEqual(self.post(f'/teams/{tid}/delete', {}, ana).status_code, 403)
        self.post(f'/teams/{tid}/delete', {}, mentor)
        self.assertIsNone(self.row('SELECT 1 FROM teams WHERE id=?', tid))
        self.assertEqual(self.row("SELECT team FROM users WHERE email='pessoa1@example.com'")[0], 'Sem equipe')
        self.assertEqual(self.post('/teams/99999/delete', {}, mentor).status_code, 404)

    def test_team_score_counts_each_challenge_once(self):
        ana, bia = self.person(1), self.person(2)
        self.post('/teams/create', {'name': 'Pontos', 'side': 'Red Team'}, ana)
        self.post(f'/teams/{self.team_id("Pontos")}/join', {}, bia)
        con = sqlite3.connect(module.DB)
        con.execute("INSERT INTO attempts(user_id,challenge_id,correct,created_at) VALUES(?,1,1,1),(?,1,1,2),(?,3,1,3)", (self.uid(1), self.uid(2), self.uid(2)))
        con.commit()
        con.close()
        con = sqlite3.connect(module.DB)
        con.row_factory = sqlite3.Row
        data = teams.overview(con)
        expected = con.execute('SELECT SUM(points) FROM challenges WHERE id IN (1,3)').fetchone()[0]
        con.close()
        team = next(item for item in data if item['name'] == 'Pontos')
        self.assertEqual((team['solved'], team['points']), (2, expected))
        self.assertEqual(len(team['members']), 2)

    def test_xss_in_team_name_is_escaped(self):
        ana = self.person(1)
        self.post('/teams/create', {'name': '<script>alert(1)</script>', 'side': 'Red Team'}, ana)
        data = ana.get('/teams').data
        self.assertNotIn(b'<script>alert(1)</script>', data)
        self.assertIn(b'&lt;script&gt;', data)


class OccurrenceTests(Base):
    def occurrence(self, client, cid=1, kind='tab_hidden'):
        return self.post(f'/challenge/{cid}/occurrence', {'kind': kind}, client)

    def test_guard_banner_only_for_unsolved_participant(self):
        ana = self.person(1)
        page = ana.get('/challenge/1')
        self.assertIn(b'data-focus-guard', page.data)
        self.assertIn(b'focus-guard.js', page.data)
        self.assertNotIn(b'data-focus-guard', self.mentor().get('/challenge/1').data)
        self.post('/challenge/1', {'flag': 'CTF{bem_vindo_ao_purple_lab}'}, ana)
        self.assertNotIn(b'data-focus-guard', ana.get('/challenge/1').data)

    def test_occurrence_recorded_and_counted_on_page(self):
        ana = self.person(1)
        ana.get('/challenge/1')
        self.assertEqual(self.occurrence(ana).status_code, 204)
        self.assertEqual(self.row('SELECT COUNT(*) FROM occurrences WHERE user_id=? AND challenge_id=1', self.uid(1))[0], 1)
        self.assertIn(b'data-count="1"', ana.get('/challenge/1').data)

    def test_rapid_duplicates_collapse_into_one(self):
        ana = self.person(1)
        for kind in ('window_blur', 'tab_hidden', 'page_leave'):
            self.occurrence(ana, kind=kind)
        self.assertEqual(self.row('SELECT COUNT(*) FROM occurrences')[0], 1)

    def test_invalid_kind_unknown_and_inactive_challenge_and_csrf(self):
        ana = self.person(1)
        self.occurrence(ana, kind='hack')
        self.assertEqual(self.row('SELECT COUNT(*) FROM occurrences')[0], 0)
        self.assertEqual(self.occurrence(ana, cid=9999).status_code, 404)
        con = sqlite3.connect(module.DB)
        con.execute('UPDATE challenges SET active=0 WHERE id=3')
        con.commit()
        con.close()
        self.assertEqual(self.occurrence(ana, cid=3).status_code, 404)
        self.assertEqual(ana.post('/challenge/1/occurrence', data={'kind': 'tab_hidden'}).status_code, 400)

    def test_no_occurrence_after_solving_or_for_mentor_or_anonymous(self):
        ana = self.person(1)
        self.post('/challenge/1', {'flag': 'CTF{bem_vindo_ao_purple_lab}'}, ana)
        self.assertEqual(self.occurrence(ana).status_code, 204)
        self.assertEqual(self.row('SELECT COUNT(*) FROM occurrences')[0], 0)
        self.assertEqual(self.occurrence(self.mentor()).status_code, 403)
        # sem sessão, o CSRF barra a requisição antes de qualquer registro
        self.assertEqual(module.app.test_client().post('/challenge/1/occurrence', data={'kind': 'tab_hidden'}).status_code, 400)
        self.assertEqual(self.row('SELECT COUNT(*) FROM occurrences')[0], 0)

    def test_per_challenge_cap(self):
        ana = self.person(1)
        con = sqlite3.connect(module.DB)
        con.row_factory = sqlite3.Row
        uid = self.uid(1)
        con.executemany('INSERT INTO occurrences(user_id,challenge_id,kind,created_at) VALUES(?,1,?,?)',
                        [(uid, 'tab_hidden', 100 + i) for i in range(occurrences.MAX_PER_CHALLENGE)])
        con.commit()
        self.assertFalse(occurrences.record(con, uid, 1, 'tab_hidden', now=10 ** 9))
        con.close()

    def test_mentor_sees_occurrences_participant_does_not(self):
        ana = self.person(1)
        self.occurrence(ana)
        mentor = self.mentor()
        page = mentor.get('/admin/occurrences')
        self.assertEqual(page.status_code, 200)
        self.assertIn(b'Pessoa 1', page.data)
        self.assertIn('Trocou de aba'.encode(), page.data)
        dossier = mentor.get(f'/participante/{self.uid(1)}')
        self.assertIn('Trocou de aba'.encode(), dossier.data)
        self.assertEqual(ana.get('/admin/occurrences').status_code, 403)

    def test_script_is_served_from_self_and_csp_allows_it(self):
        ana = self.person(1)
        csp = ana.get('/challenge/1').headers['Content-Security-Policy']
        self.assertIn("script-src 'self'", csp)
        self.assertNotIn(b'onclick', ana.get('/challenge/1').data)
        script = ana.get('/static/focus-guard.js')
        script.close()
        self.assertEqual(script.status_code, 200)


class TeamRequirementTests(Base):
    RED, BLUE, WARMUP = 3, 4, 1     # Texto estranho (Red), Quem está atacando (Blue), Boas-vindas (Aquecimento)
    RED_FLAG = 'CTF{base64_nao_e_criptografia}'

    def attempts(self):
        return self.row('SELECT COUNT(*) FROM attempts')[0]

    def test_without_team_red_and_blue_are_locked(self):
        ana = self.person(1)
        for cid in (self.RED, self.BLUE):
            page = ana.get(f'/challenge/{cid}')
            self.assertEqual(page.status_code, 200)
            self.assertIn('Desafio em equipe'.encode(), page.data)
            self.assertNotIn(b'Briefing da miss', page.data)
            self.assertNotIn(b'name="flag"', page.data)
            self.assertNotIn(b'data-focus-guard', page.data)
            self.assertEqual(self.post(f'/challenge/{cid}', {'flag': self.RED_FLAG}, ana).status_code, 403)
        self.assertEqual(self.attempts(), 0)
        # abrir o desafio bloqueado não inicia a contagem de tempo
        self.assertEqual(self.row('SELECT COUNT(*) FROM starts')[0], 0)

    def test_warmup_and_corporate_stay_free(self):
        ana = self.person(1)
        self.assertIn(b'name="flag"', ana.get(f'/challenge/{self.WARMUP}').data)
        corporate = self.row("SELECT id FROM challenges WHERE title='Meta trimestral'")[0]
        self.assertIn(b'name="flag"', ana.get(f'/challenge/{corporate}').data)
        self.post(f'/challenge/{self.WARMUP}', {'flag': 'CTF{bem_vindo_ao_purple_lab}'}, ana)
        self.assertEqual(self.attempts(), 1)

    def test_same_side_team_unlocks_and_scores(self):
        ana = self.person(1)
        self.post('/teams/create', {'name': 'Equipe Vermelha', 'side': 'Red Team'}, ana)
        page = ana.get(f'/challenge/{self.RED}')
        self.assertIn(b'name="flag"', page.data)
        self.assertIn(b'data-focus-guard', page.data)
        self.post(f'/challenge/{self.RED}', {'flag': self.RED_FLAG}, ana)
        self.assertEqual(self.row('SELECT COUNT(*) FROM attempts WHERE correct=1')[0], 1)

    def test_other_side_team_is_still_locked_with_explanation(self):
        ana = self.person(1)
        self.post('/teams/create', {'name': 'Equipe Azul', 'side': 'Blue Team'}, ana)
        page = ana.get(f'/challenge/{self.RED}')
        self.assertIn('a sua equipe é Blue Team'.encode(), page.data)
        self.assertEqual(self.post(f'/challenge/{self.RED}', {'flag': self.RED_FLAG}, ana).status_code, 403)
        self.assertIn(b'name="flag"', ana.get(f'/challenge/{self.BLUE}').data)
        self.assertEqual(self.attempts(), 0)

    def test_leaving_team_locks_again_and_keeps_history(self):
        ana = self.person(1)
        self.post('/teams/create', {'name': 'Equipe Saida', 'side': 'Red Team'}, ana)
        self.post(f'/challenge/{self.RED}', {'flag': self.RED_FLAG}, ana)
        self.post('/teams/leave', {}, ana)
        self.assertIn('Desafio em equipe'.encode(), ana.get(f'/challenge/{self.RED}').data)
        self.assertEqual(self.row('SELECT COUNT(*) FROM attempts WHERE correct=1')[0], 1)

    def test_mentor_is_exempt(self):
        page = self.mentor().get(f'/challenge/{self.RED}')
        self.assertEqual(page.status_code, 200)
        self.assertNotIn('Desafio em equipe'.encode(), page.data)
        self.assertIn(b'Briefing da miss', page.data)

    def test_lab_cannot_be_started_without_team(self):
        from unittest.mock import patch
        ana = self.person(1)
        lab = self.row("SELECT id FROM challenges WHERE image='cti-lab/web-01'")[0]   # Red Team
        with patch.object(module.orch, 'start', return_value=12345) as start:
            self.post(f'/challenge/{lab}/start', {}, ana)
            start.assert_not_called()
        self.assertEqual(self.row('SELECT COUNT(*) FROM instances')[0], 0)

    def test_blocked_user_cannot_record_occurrences(self):
        ana = self.person(1)
        self.post(f'/challenge/{self.RED}/occurrence', {'kind': 'tab_hidden'}, ana)
        self.assertEqual(self.row('SELECT COUNT(*) FROM occurrences')[0], 0)

    def test_list_shows_requirement_and_team_notice(self):
        ana = self.person(1)
        page = ana.get('/challenges')
        self.assertIn('Requer equipe Red Team'.encode(), page.data)
        self.assertIn('Entre em uma equipe'.encode(), page.data)
        self.post('/teams/create', {'name': 'Equipe Lista', 'side': 'Blue Team'}, ana)
        page = ana.get('/challenges')
        self.assertIn('Requer equipe Red Team'.encode(), page.data)
        self.assertIn('Sua equipe é'.encode(), page.data)
        self.assertNotIn('Requer equipe Blue Team'.encode(), page.data)

    def test_mentor_created_red_challenge_also_requires_team(self):
        mentor = self.mentor()
        self.post('/admin/challenges', {'title': 'Ataque novo', 'category': 'Web', 'side': 'Red Team', 'audience': 'Candidatos',
                                        'points': '100', 'description': 'Descrição longa o suficiente para valer.', 'answer': 'CTF{x}', 'active': '1'}, mentor)
        cid = self.row("SELECT id FROM challenges WHERE title='Ataque novo'")[0]
        self.assertIn('Desafio em equipe'.encode(), self.person(1).get(f'/challenge/{cid}').data)


if __name__ == '__main__':
    unittest.main()
