"""Progresso e relatos de aprendizagem, persistidos no servidor."""
import time
from flask import abort, flash, redirect, render_template, request, session

SCHEMA = """
CREATE TABLE IF NOT EXISTS writeups(user_id INTEGER NOT NULL,challenge_id INTEGER NOT NULL,
 content TEXT NOT NULL,updated_at INTEGER NOT NULL,PRIMARY KEY(user_id,challenge_id));
CREATE INDEX IF NOT EXISTS idx_attempts_progress ON attempts(user_id,challenge_id,correct);
CREATE INDEX IF NOT EXISTS idx_instances_progress ON instances(user_id,challenge_id,active,expires_at);
CREATE INDEX IF NOT EXISTS idx_evaluations_user ON evaluations(user_id);
CREATE INDEX IF NOT EXISTS idx_applications_job ON applications(job_id,user_id);
"""

def register_routes(app, db, login_required):
    @app.get('/progress')
    @login_required
    def progress():
        uid=session['user_id']
        areas=db().execute('''SELECT c.category,COUNT(*) total,
            SUM(CASE WHEN EXISTS(SELECT 1 FROM attempts a WHERE a.challenge_id=c.id
            AND a.user_id=? AND a.correct=1) THEN 1 ELSE 0 END) solved
            FROM challenges c WHERE c.active=1 GROUP BY c.category ORDER BY c.category''',(uid,)).fetchall()
        solved=db().execute('''SELECT c.id,c.title,w.content FROM challenges c
            LEFT JOIN writeups w ON w.challenge_id=c.id AND w.user_id=?
            WHERE EXISTS(SELECT 1 FROM attempts a WHERE a.challenge_id=c.id AND a.user_id=? AND a.correct=1)
            ORDER BY c.id''',(uid,uid)).fetchall()
        recent=db().execute('''SELECT c.title,a.correct FROM attempts a JOIN challenges c ON c.id=a.challenge_id
            WHERE a.user_id=? ORDER BY a.id DESC LIMIT 20''',(uid,)).fetchall()
        return render_template('progress.html',areas=areas,solved=solved,recent=recent)

    @app.post('/writeups/<int:cid>')
    @login_required
    def save_writeup(cid):
        uid=session['user_id']
        if not db().execute('SELECT 1 FROM attempts WHERE user_id=? AND challenge_id=? AND correct=1',(uid,cid)).fetchone():
            abort(403)
        content=request.form.get('content','').strip()
        if not 30 <= len(content) <= 6000:
            abort(400,description='Descreva sua investigação em 30 a 6000 caracteres.')
        db().execute('''INSERT INTO writeups VALUES(?,?,?,?) ON CONFLICT(user_id,challenge_id)
            DO UPDATE SET content=excluded.content,updated_at=excluded.updated_at''',(uid,cid,content,int(time.time())))
        db().commit()
        flash('Relato salvo no seu portfólio de aprendizagem.')
        return redirect('/progress')
