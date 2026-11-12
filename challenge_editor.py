"""Editorial local de desafios textuais. Nenhum conteúdo executa comandos."""
import hashlib
import re
import time
from flask import abort, flash, redirect, render_template, request, session

STATES = {'draft': 'Rascunho', 'published': 'Publicado', 'paused': 'Pausado'}
SIDES = ('Aquecimento', 'Blue Team', 'Red Team', 'Purple Team')


def migrate(connection):
    columns = {row[1] for row in connection.execute('PRAGMA table_info(challenges)')}
    for name, definition in (
        ('editorial_status', "TEXT NOT NULL DEFAULT 'published' CHECK(editorial_status IN ('draft','published','paused'))"),
        ('editorial_revision', 'INTEGER NOT NULL DEFAULT 1 CHECK(editorial_revision>0)'),
        ('editor_created', 'INTEGER NOT NULL DEFAULT 0 CHECK(editor_created IN (0,1))'),
    ):
        if name not in columns:
            connection.execute(f'ALTER TABLE challenges ADD COLUMN {name} {definition}')
    connection.execute('''CREATE TABLE IF NOT EXISTS challenge_history(
        id INTEGER PRIMARY KEY, challenge_id INTEGER NOT NULL REFERENCES challenges(id),
        actor_id INTEGER NOT NULL REFERENCES users(id), event TEXT NOT NULL,
        state TEXT NOT NULL, revision INTEGER NOT NULL, created_at INTEGER NOT NULL)''')
    connection.execute('CREATE INDEX IF NOT EXISTS idx_challenge_editorial ON challenges(editorial_status,id)')


def register_routes(app, db, mentor_required):
    def item(cid):
        # Never load the answer hash into a template context.
        row = db().execute('''SELECT id,title,category,side,points,description,hint,image,
            editorial_status,editorial_revision,editor_created FROM challenges WHERE id=?''', (cid,)).fetchone()
        if not row:
            abort(404)
        return dict(row)

    def attempted(cid):
        return db().execute('SELECT 1 FROM attempts WHERE challenge_id=? LIMIT 1', (cid,)).fetchone() is not None

    def values_from_form():
        names = ('title', 'category', 'side', 'points', 'description', 'hint', 'state', 'revision')
        return {name: request.form.get(name, '').strip() for name in names}

    def validate(values, existing=None, frozen=False):
        errors = {}
        allowed = {'title','category','side','points','description','hint','state','revision','answer','csrf_token'}
        if set(request.form) - allowed or any(len(request.form.getlist(name)) != 1 for name in request.form):
            errors['_form'] = 'O formulário contém campos desconhecidos ou repetidos. Recarregue e tente novamente.'
        if not 3 <= len(values['title']) <= 120:
            errors['title'] = 'Informe um título entre 3 e 120 caracteres.'
        if not 2 <= len(values['category']) <= 80:
            errors['category'] = 'Informe uma categoria entre 2 e 80 caracteres.'
        if values['side'] not in SIDES:
            errors['side'] = 'Escolha uma área válida.'
        if not re.fullmatch(r'[0-9]{1,5}', values['points']) or not 0 <= int(values['points']) <= 10000:
            errors['points'] = 'Use uma pontuação inteira entre 0 e 10000.'
        if len(values['description']) > 8000 or (values['state'] == 'published' and len(values['description']) < 20):
            errors['description'] = 'Para publicar, descreva o desafio em 20 a 8000 caracteres.'
        if len(values['hint']) > 1000:
            errors['hint'] = 'A dica aceita até 1000 caracteres.'
        if values['state'] not in STATES:
            errors['state'] = 'Escolha um estado válido.'
        answer = request.form.get('answer', '').strip()
        if len(answer) > 512 or (answer and any(ord(c) < 32 for c in answer)):
            errors['answer'] = 'Use uma resposta de até 512 caracteres, sem caracteres de controle.'
        has_answer = bool(existing and db().execute('SELECT 1 FROM challenges WHERE id=? AND flag_hash IS NOT NULL AND flag_hash!=?', (existing['id'], '')).fetchone())
        if values['state'] == 'published' and not answer and not has_answer:
            errors['answer'] = 'Defina a resposta antes de publicar.'
        if existing:
            if not existing['editor_created'] and values['title'] != existing['title']:
                errors['title'] = 'O título herdado é preservado para manter o catálogo incremental.'
            if frozen:
                if values['side'] != existing['side']:
                    errors['side'] = 'A área não muda após tentativas.'
                if values['points'] != str(existing['points']):
                    errors['points'] = 'A pontuação não muda após tentativas.'
                if answer:
                    errors['answer'] = 'A resposta não muda após tentativas. Crie outro desafio.'
        duplicate = db().execute('SELECT id FROM challenges WHERE title=? AND id!=?', (values['title'], existing['id'] if existing else -1)).fetchone()
        if duplicate:
            errors['title'] = 'Já existe um desafio com este título.'
        return errors, answer

    def render(existing, values, errors=None, code=200, conflict=False):
        return render_template('challenge_editor.html', challenge=existing, values=values,
            errors=errors or {}, states=STATES, sides=SIDES,
            frozen=attempted(existing['id']) if existing else False, conflict=conflict), code

    @app.get('/admin/challenges')
    @mentor_required
    def admin_challenges():
        rows = db().execute('''SELECT c.id,c.title,c.category,c.side,c.points,c.image,
            c.editorial_status,c.editorial_revision,COUNT(a.id) attempts
            FROM challenges c LEFT JOIN attempts a ON a.challenge_id=c.id GROUP BY c.id ORDER BY c.id DESC''').fetchall()
        return render_template('admin_challenges.html', challenges=rows, states=STATES)

    @app.route('/admin/challenges/new', methods=['GET','POST'])
    @mentor_required
    def create_challenge():
        values = dict(title='', category='', side='Blue Team', points='100', description='', hint='', state='draft', revision='')
        if request.method == 'POST':
            values = values_from_form()
            con = db(); con.execute('BEGIN IMMEDIATE')
            errors, answer = validate(values)
            if errors:
                con.rollback()
                return render(None, values, errors, 400)
            hashed = hashlib.sha256(answer.encode()).hexdigest() if answer else ''
            cursor = con.execute('''INSERT INTO challenges(title,category,side,points,description,hint,url,flag_hash,editorial_status,editor_created)
                VALUES(?,?,?,?,?,?,?, ?,?,1)''', (values['title'],values['category'],values['side'],int(values['points']),values['description'],values['hint'],'',hashed,values['state']))
            con.execute('INSERT INTO challenge_history(challenge_id,actor_id,event,state,revision,created_at) VALUES(?,?,?,?,1,?)',
                (cursor.lastrowid,session['user_id'],'created',values['state'],int(time.time())))
            con.commit()
            flash('Desafio salvo. O estado define sua disponibilidade para participantes.')
            return redirect('/admin/challenges')
        return render(None, values)

    @app.route('/admin/challenges/<int:cid>/edit', methods=['GET','POST'])
    @mentor_required
    def edit_challenge(cid):
        existing = item(cid)
        values = {key: str(existing.get(source) or '') for key, source in (
            ('title','title'),('category','category'),('side','side'),('description','description'),('hint','hint'),
            ('state','editorial_status'),('revision','editorial_revision'))}
        values['points'] = str(existing['points'])
        if request.method == 'POST':
            if existing['image']:
                abort(403, description='Laboratórios Docker têm configuração controlada e não são editados por este formulário.')
            values = values_from_form()
            con = db(); con.execute('BEGIN IMMEDIATE'); existing = item(cid)
            if not re.fullmatch(r'[0-9]{1,10}', values['revision']) or int(values['revision']) != existing['editorial_revision']:
                con.rollback()
                return render(existing, values, {'_form':'Outra edição foi salva. Recarregue os dados atuais antes de tentar novamente.'}, 409, True)
            errors, answer = validate(values, existing, attempted(cid))
            if errors:
                con.rollback()
                return render(existing, values, errors, 400)
            con.execute('''UPDATE challenges SET title=?,category=?,side=?,points=?,description=?,hint=?,editorial_status=?,
                editorial_revision=editorial_revision+1 WHERE id=?''',
                (values['title'],values['category'],values['side'],int(values['points']),values['description'],values['hint'],values['state'],cid))
            if answer:
                con.execute('UPDATE challenges SET flag_hash=? WHERE id=?', (hashlib.sha256(answer.encode()).hexdigest(),cid))
            con.execute('INSERT INTO challenge_history(challenge_id,actor_id,event,state,revision,created_at) VALUES(?,?,?,?,?,?)',
                (cid,session['user_id'],'updated',values['state'],existing['editorial_revision']+1,int(time.time())))
            con.commit()
            flash('Desafio atualizado; tentativas e pontos existentes foram preservados.')
            return redirect('/admin/challenges')
        return render(existing, values)
