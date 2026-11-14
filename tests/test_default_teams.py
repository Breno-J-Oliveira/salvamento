import os, sqlite3, tempfile, unittest
from contextlib import closing
os.environ.setdefault('SECRET_KEY', 'fixture-key')
import app, teams

class DefaultTeamsTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.old = app.DB
        app.DB = os.path.join(self.folder.name, 'test.db')
        app.app.config['TESTING'] = True
        app.init_db()
        with closing(sqlite3.connect(app.DB)) as con, con:
            for n in range(1, 6):
                con.execute("INSERT INTO users(name,email,password,role,team) VALUES(?,?,?,'participante','Sem equipe')",
                            (f'Pessoa {n}', f'user{n}@example.invalid', 'unused'))
        self.clients = []
        for n in range(1, 6):
            client = app.app.test_client()
            with client.session_transaction() as session:
                session.update(user_id=n + 1, role='participante', csrf='fixture')
            self.clients.append(client)

    def tearDown(self):
        app.DB = self.old
        self.folder.cleanup()

    def test_seed_join_capacity_leave_and_mentor_delete(self):
        with closing(sqlite3.connect(app.DB)) as con, con:
            rows = con.execute('SELECT id,name,side FROM teams ORDER BY id').fetchall()
            self.assertEqual(len(rows), 4)
            self.assertEqual(sum(row[2] == 'Red Team' for row in rows), 2)
            teams.migrate(con)
            self.assertEqual(con.execute('SELECT COUNT(*) FROM teams').fetchone()[0], 4)
            tid = rows[0][0]
        page = self.clients[0].get('/teams')
        self.assertIn(rows[0][1].encode(), page.data)
        for client in self.clients[:4]:
            self.assertEqual(client.post(f'/teams/{tid}/join', data={'csrf_token': 'fixture'}).status_code, 302)
        self.assertEqual(self.clients[4].post(f'/teams/{tid}/join', data={'csrf_token': 'fixture'}).status_code, 302)
        with closing(sqlite3.connect(app.DB)) as con, con:
            self.assertEqual(con.execute('SELECT COUNT(*) FROM team_members WHERE team_id=?', (tid,)).fetchone()[0], 4)
        for client in self.clients[:4]:
            client.post('/teams/leave', data={'csrf_token': 'fixture'})
        with closing(sqlite3.connect(app.DB)) as con, con:
            self.assertEqual(con.execute('SELECT COUNT(*) FROM teams WHERE id=?', (tid,)).fetchone()[0], 1)
        mentor = app.app.test_client()
        with mentor.session_transaction() as session:
            session.update(user_id=1, role='mentor', csrf='fixture')
        self.assertEqual(mentor.post(f'/teams/{tid}/delete', data={'csrf_token': 'fixture'}).status_code, 302)
        with closing(sqlite3.connect(app.DB)) as con, con:
            teams.migrate(con)
            self.assertEqual(con.execute('SELECT COUNT(*) FROM teams WHERE id=?', (tid,)).fetchone()[0], 0)

if __name__ == '__main__':
    unittest.main()
