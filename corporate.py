"""Avaliações internas: atribuição individual e parecer humano, sem pontos de treino."""
import sqlite3
import time
from datetime import date, datetime, timedelta
from flask import abort, flash, redirect, render_template, request, session
from vacancies import BRASILIA, deadline_label

COMPETENCIES = {'investigation': 'Investigação', 'evidence': 'Evidências', 'decisions': 'Decisões', 'communication': 'Comunicação'}
PRESETS = {
    'soc': dict(title='Investigação de acesso e exportação', context='Cenário fictício de avaliação interna. Registros autorizados: 09:00 auth-101 falha para deploy de 192.0.2.40; 09:02 auth-102 sucesso para deploy da mesma origem; 09:04 req-71 exporta relatório usando a sessão s-17. Às 09:03 houve também backup aprovado pela identidade backup-job de 198.51.100.20. O ticket de implantação confirma uma janela de manutenção, mas não informa o solicitante da exportação. Os endereços são reservados para documentação. Não há ataque ao vivo e você não deve acessar sistemas externos.', question_0='Quais registros você correlacionaria e que hipóteses concorrentes considera?', question_1='Que evidências faltam e como verificaria a legitimidade da exportação?', question_2='Que resposta proporcional recomendaria, com limites e critérios de encerramento?'),
    'access': dict(title='Mensagem suspeita e revisão de acesso', context='Cenário fictício de avaliação interna. Uma pessoa recebe mensagem alegando que precisa renovar seu acesso até 18h. O remetente usa suporte@empresa-exemplo.invalid; o diretório interno aprovado informa helpdesk@interna-exemplo.invalid. O link exibido contém o nome do portal, mas o destino informado no registro é https://renovacao-exemplo.invalid/acesso. Um pedido legítimo de revisão trimestral de acessos foi comunicado na intranet no dia anterior. Não há anexos ou mensagens reais. Não envie e-mails, não abra links e não tente autenticar: todos os elementos disponíveis estão descritos aqui.', question_0='Que sinais sustentam suas hipóteses sobre a mensagem e quais não bastam para concluir?', question_1='Como confirmaria a origem usando um canal conhecido e que informações preservaria?', question_2='Como orientaria a pessoa e a equipe, minimizando impacto e exposição de dados?')
}
STATES = {'assigned': 'Atribuída', 'draft': 'Rascunho', 'submitted': 'Aguardando revisão', 'reviewed': 'Feedback disponível'}


def migrate(con):
    con.executescript('''
    CREATE TABLE IF NOT EXISTS corporate_assessments(
        id INTEGER PRIMARY KEY, title TEXT NOT NULL, context TEXT NOT NULL,
        revision INTEGER NOT NULL DEFAULT 1, deadline_at INTEGER,
        created_by INTEGER NOT NULL REFERENCES users(id), created_at INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS corporate_questions(
        id INTEGER PRIMARY KEY, assessment_id INTEGER NOT NULL REFERENCES corporate_assessments(id),
        position INTEGER NOT NULL CHECK(position BETWEEN 0 AND 2), prompt TEXT NOT NULL,
        UNIQUE(assessment_id,position));
    CREATE TABLE IF NOT EXISTS corporate_assignments(
        id INTEGER PRIMARY KEY, assessment_id INTEGER NOT NULL REFERENCES corporate_assessments(id),
        user_id INTEGER NOT NULL REFERENCES users(id), assigned_by INTEGER NOT NULL REFERENCES users(id),
        title TEXT NOT NULL, context TEXT NOT NULL, template_revision INTEGER NOT NULL,
        deadline_at INTEGER, status TEXT NOT NULL DEFAULT 'assigned' CHECK(status IN ('assigned','draft','submitted','reviewed')),
        revision INTEGER NOT NULL DEFAULT 1, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL,
        submitted_at INTEGER, feedback TEXT NOT NULL DEFAULT '', UNIQUE(assessment_id,user_id));
    CREATE TABLE IF NOT EXISTS corporate_assignment_questions(
        id INTEGER PRIMARY KEY, assignment_id INTEGER NOT NULL REFERENCES corporate_assignments(id),
        position INTEGER NOT NULL CHECK(position BETWEEN 0 AND 2), prompt TEXT NOT NULL,
        answer TEXT NOT NULL DEFAULT '', UNIQUE(assignment_id,position));
    CREATE TABLE IF NOT EXISTS corporate_reviews(
        id INTEGER PRIMARY KEY, assignment_id INTEGER NOT NULL REFERENCES corporate_assignments(id),
        revision INTEGER NOT NULL, reviewer_id INTEGER NOT NULL REFERENCES users(id),
        investigation INTEGER NOT NULL CHECK(investigation BETWEEN 0 AND 5),
        evidence INTEGER NOT NULL CHECK(evidence BETWEEN 0 AND 5),
        decisions INTEGER NOT NULL CHECK(decisions BETWEEN 0 AND 5),
        communication INTEGER NOT NULL CHECK(communication BETWEEN 0 AND 5),
        justification TEXT NOT NULL, notes TEXT NOT NULL, feedback TEXT NOT NULL,
        created_at INTEGER NOT NULL, UNIQUE(assignment_id,revision));
    CREATE INDEX IF NOT EXISTS idx_corporate_owner ON corporate_assignments(user_id,status,id);
    CREATE INDEX IF NOT EXISTS idx_corporate_review ON corporate_reviews(assignment_id,id);
    ''')


def parse_deadline(value):
    if not value:
        return None
    try:
        day = date.fromisoformat(value)
        if not 2000 <= day.year <= 2100:
            raise ValueError()
        return int(datetime.combine(day + timedelta(days=1), datetime.min.time(), BRASILIA).timestamp())
    except (ValueError, OverflowError, OSError):
        raise ValueError('Informe uma data válida entre 2000 e 2100.')


def register_routes(app, db, login_required, mentor_required):
    def get_assignment(aid, owner=False):
        # Private review fields are deliberately not queried for employees.
        item = db().execute('SELECT a.*,u.name employee_name FROM corporate_assignments a JOIN users u ON u.id=a.user_id WHERE a.id=?', (aid,)).fetchone()
        if not item:
            abort(404)
        if owner and (session.get('role') != 'participante' or item['user_id'] != session['user_id']):
            abort(403)
        return dict(item)

    def decorate(item):
        item = dict(item)
        item['deadline_label'] = deadline_label(item)
        item['expired'] = item['deadline_at'] is not None and item['deadline_at'] <= int(time.time())
        return item

    def revision_matches(item):
        value = request.form.get('revision', '')
        return value.isascii() and value.isdigit() and len(value)<=18 and int(value) == item['revision']

    @app.get('/admin/assessments')
    @mentor_required
    def corporate_admin():
        assessments = db().execute('SELECT a.*,(SELECT COUNT(*) FROM corporate_assignments x WHERE x.assessment_id=a.id) assigned_count FROM corporate_assessments a ORDER BY a.id DESC').fetchall()
        assignments = db().execute('SELECT a.*,u.name employee_name FROM corporate_assignments a JOIN users u ON u.id=a.user_id ORDER BY a.id DESC').fetchall()
        employees = db().execute("SELECT id,name,email FROM users WHERE role='participante' ORDER BY name,id").fetchall()
        return render_template('corporate_admin.html', assessments=[decorate(a) for a in assessments], assignments=[decorate(a) for a in assignments], employees=employees, states=STATES)

    @app.route('/admin/assessments/new', methods=['GET', 'POST'])
    @app.route('/admin/assessments/<int:assessment_id>/edit', methods=['GET', 'POST'])
    @mentor_required
    def corporate_editor(assessment_id=None):
        existing = db().execute('SELECT * FROM corporate_assessments WHERE id=?', (assessment_id,)).fetchone() if assessment_id else None
        if assessment_id and not existing:
            abort(404)
        prompts = db().execute('SELECT prompt FROM corporate_questions WHERE assessment_id=? ORDER BY position', (assessment_id,)).fetchall() if existing else []
        values = dict(title=existing['title'] if existing else '', context=existing['context'] if existing else '', deadline='')
        if existing and existing['deadline_at']:
            from vacancies import deadline_value
            values['deadline'] = deadline_value(existing['deadline_at'])
        values.update({f'question_{i}': prompts[i][0] if i < len(prompts) else '' for i in range(3)})
        scenario = request.args.get('scenario','')
        if scenario and scenario not in PRESETS:
            abort(400, description='Escolha um cenário interno disponível.')
        if not existing and request.method == 'GET' and scenario:
            values.update(PRESETS[scenario])
        error = None; code = 200
        if request.method == 'POST':
            values = {key: request.form.get(key, '').strip() for key in ('title', 'context', 'deadline', 'question_0', 'question_1', 'question_2')}
            try:
                if not 3 <= len(values['title']) <= 120 or not 30 <= len(values['context']) <= 6000:
                    raise ValueError('Use título de 3 a 120 caracteres e contexto de 30 a 6000 caracteres.')
                if any(not 10 <= len(values[f'question_{i}']) <= 2000 for i in range(3)):
                    raise ValueError('Preencha as três perguntas, de 10 a 2000 caracteres cada.')
                deadline = parse_deadline(values['deadline'])
                if deadline is not None and deadline <= int(time.time()):
                    raise ValueError('Escolha um prazo futuro para novas atribuições.')
                d = db(); d.execute('BEGIN IMMEDIATE')
                if existing:
                    current = d.execute('SELECT * FROM corporate_assessments WHERE id=?', (assessment_id,)).fetchone()
                    if not revision_matches(current):
                        d.rollback(); error = 'Esta avaliação foi alterada em outra aba. Seus campos foram preservados; recarregue para revisar a versão atual.'; code = 409
                    else:
                        d.execute('UPDATE corporate_assessments SET title=?,context=?,deadline_at=?,revision=revision+1 WHERE id=?', (values['title'],values['context'],deadline,assessment_id))
                        d.execute('DELETE FROM corporate_questions WHERE assessment_id=?', (assessment_id,))
                else:
                    assessment_id = d.execute('INSERT INTO corporate_assessments(title,context,deadline_at,created_by,created_at) VALUES(?,?,?,?,?)', (values['title'],values['context'],deadline,session['user_id'],int(time.time()))).lastrowid
                if not error:
                    for i in range(3):
                        d.execute('INSERT INTO corporate_questions(assessment_id,position,prompt) VALUES(?,?,?)', (assessment_id,i,values[f'question_{i}']))
                    d.commit(); flash('Avaliação salva. Atribuições anteriores mantêm seu conteúdo e prazo.'); return redirect('/admin/assessments')
            except ValueError as exc:
                error = str(exc); code = 400
        return render_template('corporate_editor.html', values=values, assessment_id=assessment_id, revision=request.form.get('revision','') if code == 409 else existing['revision'] if existing else 0, error=error), code

    @app.post('/admin/assessments/<int:assessment_id>/assign')
    @mentor_required
    def corporate_assign(assessment_id):
        raw = request.form.get('user_id', '')
        if not raw.isascii() or not raw.isdigit() or len(raw)>18:
            abort(400, description='Escolha uma conta de participante existente.')
        d = db(); d.execute('BEGIN IMMEDIATE')
        assessment = d.execute('SELECT * FROM corporate_assessments WHERE id=?', (assessment_id,)).fetchone()
        if not assessment:
            abort(404)
        employee = d.execute("SELECT id FROM users WHERE id=? AND role='participante'", (int(raw),)).fetchone()
        if not employee:
            abort(400, description='Escolha uma conta de participante existente.')
        previous = d.execute('SELECT id FROM corporate_assignments WHERE assessment_id=? AND user_id=?', (assessment_id,employee['id'])).fetchone()
        if previous:
            d.rollback(); flash('Esta avaliação já foi atribuída a essa pessoa.'); return redirect('/admin/assessments')
        if assessment['deadline_at'] is not None and assessment['deadline_at'] <= int(time.time()):
            abort(400, description='Atualize o prazo antes de fazer novas atribuições.')
        questions = d.execute('SELECT prompt FROM corporate_questions WHERE assessment_id=? ORDER BY position', (assessment_id,)).fetchall()
        if len(questions) != 3:
            abort(400, description='Prepare as três perguntas antes de atribuir.')
        now = int(time.time())
        aid = d.execute('''INSERT INTO corporate_assignments(assessment_id,user_id,assigned_by,title,context,template_revision,deadline_at,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?)''', (assessment_id,employee['id'],session['user_id'],assessment['title'],assessment['context'],assessment['revision'],assessment['deadline_at'],now,now)).lastrowid
        for i, question in enumerate(questions):
            d.execute('INSERT INTO corporate_assignment_questions(assignment_id,position,prompt) VALUES(?,?,?)', (aid,i,question['prompt']))
        d.commit(); flash('Avaliação atribuída. A pessoa acessa pela própria conta; nenhum e-mail é enviado.'); return redirect('/admin/assessments')

    @app.get('/my-assessments')
    @login_required
    def corporate_home():
        if session.get('role') != 'participante':
            abort(403)
        assignments = db().execute('SELECT * FROM corporate_assignments WHERE user_id=? ORDER BY id DESC', (session['user_id'],)).fetchall()
        return render_template('corporate_home.html', assignments=[decorate(a) for a in assignments], states=STATES)

    @app.route('/my-assessments/<int:aid>', methods=['GET','POST'])
    @login_required
    def corporate_assignment(aid):
        assignment = get_assignment(aid, owner=True); error = None; code = 200
        questions = [dict(q) for q in db().execute('SELECT id,position,prompt,answer FROM corporate_assignment_questions WHERE assignment_id=? ORDER BY position', (aid,))]
        if request.method == 'POST':
            action = request.form.get('action')
            if action not in ('save','submit'):
                abort(400)
            if assignment['status'] in ('submitted','reviewed'):
                return redirect(f'/my-assessments/{aid}')
            for q in questions:
                q['answer'] = request.form.get(f'answer_{q["id"]}', '').strip()
            if any(len(q['answer'])>6000 for q in questions) or (action == 'submit' and any(len(q['answer'])<30 for q in questions)):
                error = 'Ao enviar, cada análise precisa de 30 a 6000 caracteres. O rascunho pode ficar incompleto.'; code = 400
            else:
                d = db(); d.execute('BEGIN IMMEDIATE')
                current = dict(d.execute('SELECT * FROM corporate_assignments WHERE id=?', (aid,)).fetchone())
                if current['status'] in ('submitted','reviewed'):
                    d.rollback(); return redirect(f'/my-assessments/{aid}')
                if not revision_matches(current):
                    error = 'As respostas mudaram em outra aba. Seu texto foi preservado; recarregue e confira antes de salvar.'; code = 409
                elif current['deadline_at'] is not None and current['deadline_at'] <= int(time.time()):
                    error = 'O prazo terminou. As respostas já salvas foram preservadas; novos envios não são aceitos.'; code = 400
                else:
                    for q in questions:
                        d.execute('UPDATE corporate_assignment_questions SET answer=? WHERE id=? AND assignment_id=?', (q['answer'],q['id'],aid))
                    now = int(time.time())
                    d.execute('UPDATE corporate_assignments SET status=?,submitted_at=?,updated_at=?,revision=revision+1 WHERE id=?', ('submitted' if action=='submit' else 'draft',now if action=='submit' else None,now,aid))
                    d.commit(); flash('Avaliação enviada para revisão humana.' if action=='submit' else 'Rascunho salvo.'); return redirect(f'/my-assessments/{aid}')
                d.rollback()
        return render_template('corporate_assignment.html', assignment=decorate(assignment), questions=questions, review=None, reviews=[], competencies=COMPETENCIES, states=STATES, mentor=False, error=error, form_revision=request.form.get('revision','') if code==409 else assignment['revision']), code

    @app.route('/admin/assessments/assignments/<int:aid>', methods=['GET','POST'])
    @mentor_required
    def corporate_review(aid):
        assignment = get_assignment(aid); error = None; code = 200
        if request.method == 'POST':
            if assignment['status'] not in ('submitted','reviewed'):
                abort(400, description='A pessoa precisa enviar a avaliação antes do parecer.')
            try:
                scores = [int(request.form.get(key,'')) for key in COMPETENCIES]
                justification = request.form.get('justification','').strip(); notes = request.form.get('notes','').strip(); feedback = request.form.get('feedback','').strip()
                if any(n<0 or n>5 for n in scores) or not 30 <= len(justification) <= 4000 or len(notes)>4000 or not 10 <= len(feedback) <= 4000:
                    raise ValueError()
            except ValueError:
                error = 'Confira as quatro notas (0 a 5), justificativa de 30 a 4000 caracteres, nota interna até 4000 e feedback de 10 a 4000.'; code = 400
            if not error:
                d = db(); d.execute('BEGIN IMMEDIATE')
                current = dict(d.execute('SELECT * FROM corporate_assignments WHERE id=?', (aid,)).fetchone())
                if not revision_matches(current):
                    d.rollback(); error = 'Outro parecer foi salvo. Seus campos foram preservados; recarregue para conferir a revisão atual.'; code = 409
                else:
                    now = int(time.time())
                    d.execute('''INSERT INTO corporate_reviews(assignment_id,revision,reviewer_id,investigation,evidence,decisions,communication,justification,notes,feedback,created_at)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?)''', (aid,current['revision']+1,session['user_id'],*scores,justification,notes,feedback,now))
                    d.execute("UPDATE corporate_assignments SET status='reviewed',feedback=?,updated_at=?,revision=revision+1 WHERE id=?", (feedback,now,aid))
                    d.commit(); flash('Revisão registrada. Apenas o feedback foi compartilhado com a pessoa avaliada.'); return redirect(f'/admin/assessments/assignments/{aid}')
        questions = db().execute('SELECT id,position,prompt,answer FROM corporate_assignment_questions WHERE assignment_id=? ORDER BY position', (aid,)).fetchall()
        reviews = [dict(r) for r in db().execute('SELECT r.*,u.name reviewer_name FROM corporate_reviews r JOIN users u ON u.id=r.reviewer_id WHERE assignment_id=? ORDER BY r.id DESC', (aid,))]
        return render_template('corporate_assignment.html', assignment=decorate(assignment), questions=questions, review=reviews[0] if reviews else None, reviews=reviews, competencies=COMPETENCIES, states=STATES, mentor=True, error=error, form_revision=request.form.get('revision','') if code==409 else assignment['revision']), code
