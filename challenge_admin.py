"""Criação e gestão de desafios pela mentoria (qualquer área, não só cibersegurança)."""
import hashlib
import time
from flask import abort, flash, redirect, render_template, request, session

SIDES = ('Corporativo', 'Red Team', 'Blue Team', 'Aquecimento')
AUDIENCES = ('Candidatos', 'Colaboradores', 'Todos')
CATEGORY_SUGGESTIONS = (
    'Atendimento ao cliente', 'Vendas e comercial', 'Recursos humanos', 'Financeiro', 'Jurídico e compliance',
    'Logística e operações', 'Qualidade e produção', 'Saúde e segurança do trabalho', 'Marketing e comunicação',
    'Liderança e gestão', 'Dados e planilhas', 'Segurança da informação', 'Tecnologia', 'Criptografia', 'Web',
    'Análise de logs', 'Forense', 'Hardening', 'Resposta a incidentes',
)
COLUMNS = {'active': 'INTEGER NOT NULL DEFAULT 1', 'audience': "TEXT NOT NULL DEFAULT 'Candidatos'",
           'created_by': 'INTEGER', 'updated_at': 'INTEGER'}


def migrate(con):
    """Acrescenta colunas de gestão sem tocar em respostas, pontos ou tentativas existentes."""
    existing = {r[1] for r in con.execute('PRAGMA table_info(challenges)')}
    for column, definition in COLUMNS.items():
        if column not in existing:
            con.execute(f'ALTER TABLE challenges ADD COLUMN {column} {definition}')


def answer_hash(value):
    return hashlib.sha256(value.strip().encode()).hexdigest()


def clean(form, current=None):
    """Valida o formulário e devolve (dados, erros). `current` é a linha existente na edição."""
    editing_lab = bool(current and current['image'])
    data = {k: (form.get(k) or '').strip() for k in ('title', 'category', 'side', 'audience', 'description', 'answer')}
    errors = []
    if not 3 <= len(data['title']) <= 120:
        errors.append('O título deve ter de 3 a 120 caracteres.')
    if not 2 <= len(data['category']) <= 60:
        errors.append('A categoria (área) deve ter de 2 a 60 caracteres.')
    if data['side'] not in SIDES:
        errors.append('Escolha uma trilha da lista.')
    if data['audience'] not in AUDIENCES:
        errors.append('Escolha o público do desafio.')
    if not 20 <= len(data['description']) <= 4000:
        errors.append('O briefing deve ter de 20 a 4000 caracteres.')
    try:
        data['points'] = int(form.get('points', ''))
    except ValueError:
        data['points'] = None
    if data['points'] is None or not 10 <= data['points'] <= 1000:
        errors.append('A pontuação deve ser um número inteiro entre 10 e 1000.')
    if editing_lab:
        # A flag de desafios com ambiente é gerada por instância; não é editável aqui.
        data['answer'] = ''
    elif current is None and not data['answer']:
        errors.append('Informe a resposta correta.')
    if len(data['answer']) > 200:
        errors.append('A resposta correta pode ter até 200 caracteres.')
    return data, errors


def title_taken(con, title, ignore_id=None):
    row = con.execute('SELECT id FROM challenges WHERE lower(title)=lower(?) AND id IS NOT ?', (title, ignore_id)).fetchone()
    return row is not None


def usage(con, challenge_id):
    """Quantos registros de participantes dependem deste desafio."""
    count = lambda sql: con.execute(sql, (challenge_id,)).fetchone()[0]
    return dict(attempts=count('SELECT COUNT(*) FROM attempts WHERE challenge_id=?'),
                solvers=count('SELECT COUNT(DISTINCT user_id) FROM attempts WHERE challenge_id=? AND correct=1'),
                instances=count('SELECT COUNT(*) FROM instances WHERE challenge_id=?'),
                writeups=count('SELECT COUNT(*) FROM writeups WHERE challenge_id=?'))


def register_routes(app, db, mentor_required):
    fmt = lambda t: time.strftime('%d/%m/%Y %H:%M', time.localtime(t)) if t else ''

    def listing():
        return db().execute('''SELECT c.*,
              (SELECT COUNT(DISTINCT user_id) FROM attempts a WHERE a.challenge_id=c.id AND a.correct=1) solvers,
              (SELECT COUNT(*) FROM attempts a WHERE a.challenge_id=c.id) attempts
              FROM challenges c ORDER BY c.active DESC,c.id DESC''').fetchall()

    def page(template, status=200, **context):
        return render_template(template, sides=SIDES, audiences=AUDIENCES, suggestions=CATEGORY_SUGGESTIONS, **context), status

    @app.route('/admin/challenges', methods=['GET', 'POST'])
    @mentor_required
    def admin_challenges():
        d = db()
        data, errors = {}, []
        if request.method == 'POST':
            data, errors = clean(request.form)
            if not errors and title_taken(d, data['title']):
                errors.append('Já existe um desafio com este título. Use um título diferente.')
            if not errors:
                now = int(time.time())
                d.execute('INSERT INTO challenges(title,category,side,points,description,hint,url,flag_hash,audience,active,created_by,updated_at) '
                          'VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                          (data['title'], data['category'], data['side'], data['points'], data['description'], '', '',
                           answer_hash(data['answer']), data['audience'], 1 if request.form.get('active') else 0, session['user_id'], now))
                d.commit()
                flash('Desafio publicado para os participantes.' if request.form.get('active') else 'Desafio salvo como inativo.')
                return redirect('/admin/challenges')
        return page('admin_challenges.html', 400 if errors else 200, items=listing(), c=data, errors=errors, fmt=fmt)

    @app.route('/admin/challenges/<int:cid>', methods=['GET', 'POST'])
    @mentor_required
    def admin_challenge_edit(cid):
        d = db()
        row = d.execute('SELECT * FROM challenges WHERE id=?', (cid,)).fetchone()
        if not row:
            abort(404)
        errors = []
        if request.method == 'POST':
            data, errors = clean(request.form, row)
            if not errors and title_taken(d, data['title'], cid):
                errors.append('Já existe outro desafio com este título.')
            if not errors:
                sets = ['title=?', 'category=?', 'side=?', 'points=?', 'description=?', 'audience=?', 'active=?', 'updated_at=?']
                values = [data['title'], data['category'], data['side'], data['points'], data['description'],
                          data['audience'], 1 if request.form.get('active') else 0, int(time.time())]
                if data['answer']:
                    sets.append('flag_hash=?')
                    values.append(answer_hash(data['answer']))
                d.execute(f"UPDATE challenges SET {', '.join(sets)} WHERE id=?", (*values, cid))
                d.commit()
                flash('Desafio atualizado.')
                return redirect('/admin/challenges')
            row = dict(row, **{k: v for k, v in data.items() if k != 'answer'}, active=1 if request.form.get('active') else 0)
        return page('admin_challenge_edit.html', 400 if errors else 200, c=row, errors=errors, use=usage(d, cid))

    @app.post('/admin/challenges/<int:cid>/toggle')
    @mentor_required
    def admin_challenge_toggle(cid):
        d = db()
        if not d.execute('UPDATE challenges SET active=1-active,updated_at=? WHERE id=?', (int(time.time()), cid)).rowcount:
            abort(404)
        d.commit()
        flash('Visibilidade do desafio atualizada.')
        return redirect('/admin/challenges')

    @app.post('/admin/challenges/<int:cid>/delete')
    @mentor_required
    def admin_challenge_delete(cid):
        d = db()
        row = d.execute('SELECT * FROM challenges WHERE id=?', (cid,)).fetchone()
        if not row:
            abort(404)
        if row['created_by'] is None or row['image']:
            # Desafios do catálogo seriam recriados na próxima inicialização; basta desativá-los.
            flash('Desafios do catálogo da plataforma não são excluídos: desative-os para ocultá-los dos participantes.')
            return redirect('/admin/challenges')
        use = usage(d, cid)
        if use['attempts'] or use['instances'] or use['writeups']:
            flash('Este desafio já tem respostas de participantes. Desative-o para preservar o histórico e o ranking.')
            return redirect('/admin/challenges')
        d.execute('DELETE FROM starts WHERE challenge_id=?', (cid,))
        d.execute('DELETE FROM challenges WHERE id=?', (cid,))
        d.commit()
        flash('Desafio excluído.')
        return redirect('/admin/challenges')
