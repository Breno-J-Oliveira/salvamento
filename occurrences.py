"""Ocorrências de foco: registra quando o participante deixa a tela de um desafio em andamento.

O navegador não permite impedir que alguém troque de aba ou feche a janela; a página avisa,
pede confirmação ao sair e registra cada saída para revisão humana pela mentoria.
Uma ocorrência é um indicador, não prova de irregularidade.
"""
import time
from flask import abort, render_template, request, session

import teams

KINDS = {
    'tab_hidden': 'Trocou de aba ou minimizou a janela',
    'window_blur': 'Saiu da janela do desafio',
    'fullscreen_exit': 'Saiu da tela cheia',
    'page_leave': 'Tentou sair da página',
}
DEDUP_SECONDS = 2      # uma troca de aba dispara vários eventos do navegador; contam como um só
MAX_PER_CHALLENGE = 200

SCHEMA = """
CREATE TABLE IF NOT EXISTS occurrences(
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  challenge_id INTEGER NOT NULL REFERENCES challenges(id),
  kind TEXT NOT NULL,
  created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_occurrences_user ON occurrences(user_id,challenge_id,created_at);
"""


def migrate(con):
    con.executescript(SCHEMA)


def count(con, user_id, challenge_id):
    return con.execute('SELECT COUNT(*) FROM occurrences WHERE user_id=? AND challenge_id=?',
                       (user_id, challenge_id)).fetchone()[0]


def record(con, user_id, challenge_id, kind, now=None):
    """Grava uma ocorrência; devolve False quando ignorada (duplicada ou acima do limite)."""
    now = int(time.time()) if now is None else now
    if kind not in KINDS:
        return False
    recent = con.execute('SELECT 1 FROM occurrences WHERE user_id=? AND challenge_id=? AND created_at>?',
                         (user_id, challenge_id, now - DEDUP_SECONDS)).fetchone()
    if recent or count(con, user_id, challenge_id) >= MAX_PER_CHALLENGE:
        return False
    con.execute('INSERT INTO occurrences(user_id,challenge_id,kind,created_at) VALUES(?,?,?,?)',
                (user_id, challenge_id, kind, now))
    con.commit()
    return True


def for_user(con, user_id):
    return con.execute('''SELECT o.kind,o.created_at,c.title FROM occurrences o JOIN challenges c ON c.id=o.challenge_id
                          WHERE o.user_id=? ORDER BY o.id DESC LIMIT 100''', (user_id,)).fetchall()


def register_routes(app, db, login_required, mentor_required):
    fmt = lambda t: time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(t))

    @app.post('/challenge/<int:cid>/occurrence')
    @login_required
    def challenge_occurrence(cid):
        if session.get('role') != 'participante':
            abort(403)
        d, uid = db(), session['user_id']
        challenge = d.execute('SELECT active,side FROM challenges WHERE id=?', (cid,)).fetchone()
        if not challenge or not challenge['active']:
            abort(404)
        if teams.team_block(d, uid, challenge):
            return '', 204   # sem acesso ao desafio, não há tela a proteger
        solved = d.execute('SELECT 1 FROM attempts WHERE user_id=? AND challenge_id=? AND correct=1', (uid, cid)).fetchone()
        if not solved:
            record(d, uid, cid, request.form.get('kind', ''))
        return '', 204

    @app.get('/admin/occurrences')
    @mentor_required
    def admin_occurrences():
        d = db()
        summary = d.execute('''SELECT u.id,u.name,u.team,COUNT(*) total,MAX(o.created_at) last_at
                               FROM occurrences o JOIN users u ON u.id=o.user_id
                               GROUP BY u.id ORDER BY total DESC,last_at DESC''').fetchall()
        recent = d.execute('''SELECT o.kind,o.created_at,u.id user_id,u.name,c.title FROM occurrences o
                              JOIN users u ON u.id=o.user_id JOIN challenges c ON c.id=o.challenge_id
                              ORDER BY o.id DESC LIMIT 200''').fetchall()
        return render_template('admin_occurrences.html', summary=summary, recent=recent, kinds=KINDS, fmt=fmt)
