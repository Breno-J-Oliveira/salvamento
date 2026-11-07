"""Revisão humana versionada da avaliação seletiva, independente do treino."""
import time
from flask import abort, flash, redirect, render_template, request, session

LABELS = {
    'investigation': 'Investigação e formulação de hipóteses',
    'evidence': 'Uso e correlação de evidências',
    'decisions': 'Justificativa e proporcionalidade das decisões',
    'communication': 'Clareza e comunicação técnica',
}
SCHEMA = '''CREATE TABLE IF NOT EXISTS selection_reviews(
 id INTEGER PRIMARY KEY, application_id INTEGER NOT NULL,
 revision INTEGER NOT NULL CHECK(revision>=1), reviewer_id INTEGER NOT NULL,
 investigation INTEGER NOT NULL CHECK(investigation BETWEEN 0 AND 5),
 evidence INTEGER NOT NULL CHECK(evidence BETWEEN 0 AND 5),
 decisions INTEGER NOT NULL CHECK(decisions BETWEEN 0 AND 5),
 communication INTEGER NOT NULL CHECK(communication BETWEEN 0 AND 5),
 justification TEXT NOT NULL CHECK(length(justification) BETWEEN 30 AND 4000),
 created_at INTEGER NOT NULL, rubric_version INTEGER NOT NULL DEFAULT 1,
 UNIQUE(application_id,revision),
 FOREIGN KEY(application_id) REFERENCES applications(id),
 FOREIGN KEY(reviewer_id) REFERENCES users(id));
CREATE INDEX IF NOT EXISTS idx_selection_reviews_application ON selection_reviews(application_id,revision DESC);
'''


def migrate(connection):
    connection.executescript(SCHEMA)


def register_routes(app, db, mentor_required):
    def data(aid):
        # A chamada pode existir no contexto global, mas não carrega notas privadas para candidatos.
        if session.get('role') != 'mentor':
            return None
        history = [dict(r) for r in db().execute('''SELECT r.*,u.name reviewer_name
            FROM selection_reviews r JOIN users u ON u.id=r.reviewer_id
            WHERE r.application_id=? ORDER BY r.revision DESC''', (aid,))]
        for review in history:
            review['reviewed_at'] = time.strftime('%d/%m/%Y %H:%M UTC', time.gmtime(review['created_at']))
        ready = db().execute('''SELECT 1 FROM selection_assessments
            WHERE application_id=? AND submitted_at IS NOT NULL''', (aid,)).fetchone() is not None
        return dict(labels=LABELS, latest=history[0] if history else None,
                    history=history, revision=history[0]['revision'] if history else 0,
                    assessment_ready=ready)

    app.context_processor(lambda: dict(selection_rubric=data))

    @app.post('/admin/applications/<int:aid>/rubric')
    @mentor_required
    def review_selection(aid):
        connection = db()
        application = connection.execute("SELECT id,status FROM applications WHERE id=? AND status!='draft'", (aid,)).fetchone()
        if not application:
            abort(404)
        def invalid(message, code=400):
            return render_template('rubric_review.html', application_id=aid, rubric=data(aid),
                                   values=request.form, error=message), code
        try:
            revision = int(request.form.get('revision', ''))
            scores = [int(request.form.get(key, '')) for key in LABELS]
        except (ValueError, TypeError):
            return invalid('Informe a revisão e notas inteiras de 0 a 5 para todas as competências.')
        if revision < 0 or any(score < 0 or score > 5 for score in scores):
            return invalid('Informe a revisão atual e notas inteiras de 0 a 5.')
        justification = request.form.get('justification', '').strip()
        if not 30 <= len(justification) <= 4000:
            return invalid('Justifique a revisão em 30 a 4000 caracteres, citando evidências da avaliação.')
        connection.execute('BEGIN IMMEDIATE')
        # Revalida dentro da transação para não revisar um rascunho ou avaliação ainda incompleta.
        eligible = connection.execute('''SELECT 1 FROM applications a JOIN selection_assessments s ON s.application_id=a.id
            WHERE a.id=? AND a.status!='draft' AND s.submitted_at IS NOT NULL''', (aid,)).fetchone()
        if not eligible:
            connection.rollback()
            return invalid('Conclua o envio da avaliação seletiva antes de registrar a rubrica.')
        current = connection.execute('SELECT COALESCE(MAX(revision),0) FROM selection_reviews WHERE application_id=?', (aid,)).fetchone()[0]
        if current != revision:
            connection.rollback()
            return invalid('Outra revisão foi registrada. Recarregue o parecer atual antes de salvar; seus campos foram preservados.', 409)
        connection.execute('''INSERT INTO selection_reviews(application_id,revision,reviewer_id,
            investigation,evidence,decisions,communication,justification,created_at)
            VALUES(?,?,?,?,?,?,?,?,?)''', (aid, current+1, session['user_id'], *scores, justification, int(time.time())))
        connection.commit()
        flash('Rubrica registrada. A revisão humana não altera automaticamente a etapa da candidatura.')
        return redirect(f'/admin/applications/{aid}')
