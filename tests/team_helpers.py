"""Apoio aos testes: desafios Red/Blue Team exigem que o participante esteja em uma equipe do mesmo lado."""
import sqlite3
from contextlib import closing


def put_in_team(db_path, user_id, side, name=None):
    """Coloca o usuário em uma equipe do lado indicado, saindo de qualquer equipe anterior."""
    name = name or f'Equipe de teste {side} {user_id}'
    with closing(sqlite3.connect(db_path)) as con, con:
        con.execute('DELETE FROM team_members WHERE user_id=?', (user_id,))
        con.execute('INSERT OR IGNORE INTO teams(name,side,created_at) VALUES(?,?,0)', (name, side))
        team_id = con.execute('SELECT id FROM teams WHERE name=?', (name,)).fetchone()[0]
        con.execute('INSERT INTO team_members(team_id,user_id,joined_at) VALUES(?,?,0)', (team_id, user_id))
