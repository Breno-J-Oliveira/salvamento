"""Equipes Red Team e Blue Team: até 4 pessoas por equipe, uma equipe por participante."""
import sqlite3
import time
from flask import abort, flash, redirect, render_template, request, session

SIDES = ('Red Team', 'Blue Team')
MAX_MEMBERS = 4
NO_TEAM = 'Sem equipe'

SCHEMA = """
CREATE TABLE IF NOT EXISTS teams(
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  side TEXT NOT NULL CHECK(side IN ('Red Team','Blue Team')),
  created_by INTEGER REFERENCES users(id),
  created_at INTEGER NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_teams_name ON teams(lower(name));
CREATE TABLE IF NOT EXISTS team_members(
  team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
  joined_at INTEGER NOT NULL,
  PRIMARY KEY(team_id, user_id)
);
"""


def migrate(con):
    con.executescript(SCHEMA)
    con.execute('CREATE TABLE IF NOT EXISTS team_defaults_initialized (id INTEGER PRIMARY KEY CHECK(id=1))')
    if con.execute('INSERT OR IGNORE INTO team_defaults_initialized(id) VALUES(1)').rowcount:
        now = int(time.time())
        for name, side in [('Red Team Alpha', 'Red Team'), ('Red Team Beta', 'Red Team'),
                           ('Blue Team Alpha', 'Blue Team'), ('Blue Team Beta', 'Blue Team')]:
            con.execute('INSERT OR IGNORE INTO teams(name,side,created_by,created_at) VALUES(?,?,NULL,?)', (name, side, now))


def user_side(con, user_id):
    """Lado da equipe do usuário (Red Team, Blue Team) ou None se estiver sem equipe."""
    row = con.execute('SELECT t.side FROM team_members tm JOIN teams t ON t.id=tm.team_id WHERE tm.user_id=?',
                      (user_id,)).fetchone()
    return row[0] if row else None


def team_block(con, user_id, challenge):
    """Mensagem de bloqueio quando o desafio é de equipe e o usuário não cumpre a regra; senão None.

    Desafios Red Team e Blue Team exigem participar de uma equipe do mesmo lado.
    Aquecimento e Corporativo continuam livres.
    """
    needed = challenge['side']
    if needed not in SIDES:
        return None
    mine = user_side(con, user_id)
    if mine == needed:
        return None
    if mine is None:
        return f'Este desafio é resolvido em equipe. Entre em uma equipe {needed} (ou crie a sua) para abrir o briefing e enviar respostas.'
    return f'Este desafio é da trilha {needed}, mas a sua equipe é {mine}. Escolha um desafio da trilha da sua equipe.'


def clean_name(value):
    name = ' '.join((value or '').split())
    if not 3 <= len(name) <= 40:
        return None, 'O nome da equipe deve ter de 3 a 40 caracteres.'
    return name, None


def overview(con):
    """Equipes com integrantes e pontuação. Cada desafio conta uma vez por equipe."""
    teams = [dict(r) for r in con.execute('SELECT * FROM teams ORDER BY side,lower(name)')]
    by_id = {t['id']: t for t in teams}
    for team in teams:
        team.update(members=[], solved=0, points=0)
    members = con.execute('''SELECT tm.team_id,u.id user_id,u.name,tm.joined_at,
              (SELECT COUNT(DISTINCT a.challenge_id) FROM attempts a WHERE a.user_id=u.id AND a.correct=1) solved
              FROM team_members tm JOIN users u ON u.id=tm.user_id ORDER BY tm.joined_at,u.id''')
    for row in members:
        by_id[row['team_id']]['members'].append(dict(row))
    scores = con.execute('''SELECT x.team_id,COUNT(*) solved,COALESCE(SUM(c.points),0) points FROM
              (SELECT DISTINCT tm.team_id,a.challenge_id FROM team_members tm
               JOIN attempts a ON a.user_id=tm.user_id AND a.correct=1) x
              JOIN challenges c ON c.id=x.challenge_id GROUP BY x.team_id''')
    for row in scores:
        by_id[row['team_id']].update(solved=row['solved'], points=row['points'])
    for team in teams:
        team['free'] = MAX_MEMBERS - len(team['members'])
    return teams


def register_routes(app, db, login_required, mentor_required):
    def participant_only():
        if session.get('role') != 'participante':
            abort(403, description='Somente participantes entram em equipes.')

    def set_label(d, user_id, label):
        d.execute('UPDATE users SET team=? WHERE id=?', (label, user_id))

    def drop_if_empty(d, team_id):
        d.execute('DELETE FROM teams WHERE id=? AND created_by IS NOT NULL '
                  'AND NOT EXISTS (SELECT 1 FROM team_members WHERE team_id=?)', (team_id, team_id))

    @app.get('/teams')
    @login_required
    def teams_page():
        teams = overview(db())
        uid = session['user_id']
        mine = next((t for t in teams if any(m['user_id'] == uid for m in t['members'])), None)
        return render_template('teams.html', teams=teams, mine=mine, sides=SIDES, max_members=MAX_MEMBERS,
                               red=[t for t in teams if t['side'] == 'Red Team'],
                               blue=[t for t in teams if t['side'] == 'Blue Team'])

    @app.post('/teams/create')
    @login_required
    def team_create():
        participant_only()
        d, uid = db(), session['user_id']
        name, error = clean_name(request.form.get('name'))
        side = request.form.get('side', '')
        if error or side not in SIDES:
            flash(error or 'Escolha Red Team ou Blue Team.')
            return redirect('/teams')
        d.execute('BEGIN IMMEDIATE')
        if d.execute('SELECT 1 FROM team_members WHERE user_id=?', (uid,)).fetchone():
            d.rollback()
            flash('Você já faz parte de uma equipe. Saia dela antes de criar outra.')
            return redirect('/teams')
        try:
            now = int(time.time())
            team_id = d.execute('INSERT INTO teams(name,side,created_by,created_at) VALUES(?,?,?,?)',
                                (name, side, uid, now)).lastrowid
            d.execute('INSERT INTO team_members(team_id,user_id,joined_at) VALUES(?,?,?)', (team_id, uid, now))
            set_label(d, uid, name)
            d.commit()
        except sqlite3.IntegrityError:
            d.rollback()
            flash('Já existe uma equipe com este nome. Escolha outro.')
            return redirect('/teams')
        flash(f'Equipe {name} criada. Convide até {MAX_MEMBERS - 1} pessoas para completar o time.')
        return redirect('/teams')

    @app.post('/teams/<int:tid>/join')
    @login_required
    def team_join(tid):
        participant_only()
        d, uid = db(), session['user_id']
        d.execute('BEGIN IMMEDIATE')
        team = d.execute('SELECT * FROM teams WHERE id=?', (tid,)).fetchone()
        if not team:
            d.rollback()
            abort(404)
        if d.execute('SELECT 1 FROM team_members WHERE user_id=?', (uid,)).fetchone():
            d.rollback()
            flash('Você já faz parte de uma equipe. Saia dela antes de entrar em outra.')
            return redirect('/teams')
        if d.execute('SELECT COUNT(*) FROM team_members WHERE team_id=?', (tid,)).fetchone()[0] >= MAX_MEMBERS:
            d.rollback()
            flash(f'A equipe {team["name"]} já tem {MAX_MEMBERS} integrantes.')
            return redirect('/teams')
        d.execute('INSERT INTO team_members(team_id,user_id,joined_at) VALUES(?,?,?)', (tid, uid, int(time.time())))
        set_label(d, uid, team['name'])
        d.commit()
        flash(f'Você entrou na equipe {team["name"]} ({team["side"]}).')
        return redirect('/teams')

    @app.post('/teams/leave')
    @login_required
    def team_leave():
        participant_only()
        d, uid = db(), session['user_id']
        row = d.execute('SELECT team_id FROM team_members WHERE user_id=?', (uid,)).fetchone()
        if not row:
            flash('Você não está em nenhuma equipe.')
            return redirect('/teams')
        d.execute('DELETE FROM team_members WHERE user_id=?', (uid,))
        set_label(d, uid, NO_TEAM)
        drop_if_empty(d, row['team_id'])
        d.commit()
        flash('Você saiu da equipe.')
        return redirect('/teams')

    @app.post('/teams/<int:tid>/remove/<int:uid>')
    @mentor_required
    def team_remove_member(tid, uid):
        d = db()
        if not d.execute('DELETE FROM team_members WHERE team_id=? AND user_id=?', (tid, uid)).rowcount:
            abort(404)
        set_label(d, uid, NO_TEAM)
        drop_if_empty(d, tid)
        d.commit()
        flash('Integrante removido da equipe.')
        return redirect('/teams')

    @app.post('/teams/<int:tid>/delete')
    @mentor_required
    def team_delete(tid):
        d = db()
        if not d.execute('SELECT 1 FROM teams WHERE id=?', (tid,)).fetchone():
            abort(404)
        for row in d.execute('SELECT user_id FROM team_members WHERE team_id=?', (tid,)).fetchall():
            set_label(d, row['user_id'], NO_TEAM)
        d.execute('DELETE FROM team_members WHERE team_id=?', (tid,))
        d.execute('DELETE FROM teams WHERE id=?', (tid,))
        d.commit()
        flash('Equipe desfeita.')
        return redirect('/teams')
