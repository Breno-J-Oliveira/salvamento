"""Recrutamento: formulários versionados e inscrições independentes do treino."""
import json
import re
import time
from datetime import datetime, timedelta, timezone
import vacancies
from urllib.parse import urlsplit, unquote
from flask import abort, flash, redirect, render_template, request, session
from itsdangerous import TimestampSigner, BadSignature

STATUSES = {'draft':'Rascunho','submitted':'Enviada','review':'Em avaliação','interview':'Entrevista','selected':'Aprovada','rejected':'Não selecionada','withdrawn':'Desistência'}

def safe_next(value):
    if not isinstance(value, str) or len(value)>500:
        return ''
    decoded=unquote(value)
    if not decoded.startswith('/') or decoded.startswith('//') or '\\' in decoded or any(ord(c)<32 for c in decoded):
        return ''
    parts=urlsplit(decoded)
    return value if not parts.scheme and not parts.netloc else ''

def defaults(side):
    topic = 'Experiência com revisão de código e aplicações' if side == 'Red Team' else 'Experiência com investigação de logs e alertas'
    return [dict(id='availability',label='Qual sua disponibilidade?',type='text',required=True,options=[]),dict(id='experience',label=topic,type='textarea',required=True,options=[]),dict(id='portfolio',label='Link de projeto ou portfólio (opcional)',type='url',required=False,options=[])]

def validate_questions(questions):
    if not isinstance(questions,list) or not 1<=len(questions)<=15:
        raise ValueError('Defina entre 1 e 15 perguntas.')
    clean=[];seen=set()
    for q in questions:
        if not isinstance(q,dict) or set(q)-{'id','label','type','required','options'}:
            raise ValueError('Cada pergunta precisa de identificador, rótulo, tipo, obrigatoriedade e opções.')
        key=q.get('id','');label=q.get('label','');kind=q.get('type','text');required=q.get('required',False);options=q.get('options',[])
        if not isinstance(key,str) or not re.fullmatch('[a-zA-Z][a-zA-Z0-9_]{0,39}',key) or key in seen or not isinstance(label,str) or not 3<=len(label.strip())<=200 or kind not in ('text','textarea','select','multiselect','number','url') or not isinstance(required,bool):
            raise ValueError('Confira identificadores únicos, rótulos, tipos e obrigatoriedade.')
        if not isinstance(options,list) or len(options)>20 or any(not isinstance(o,str) or not 1<=len(o.strip())<=100 for o in options) or len(set(options))!=len(options) or (kind in ('select','multiselect') and not options):
            raise ValueError('Defina opções únicas e válidas para as seleções.')
        seen.add(key);clean.append(dict(id=key,label=label.strip(),type=kind,required=required,options=options if kind in ('select','multiselect') else []))
    return clean


def parse_editor(form):
    try:count=int(form.get('question_count',''))
    except ValueError:raise ValueError('Informe a quantidade de perguntas.')
    if not 1<=count<=15:raise ValueError('Defina entre 1 e 15 perguntas.')
    questions=[]
    allowed={'csrf_token','question_count'}
    for index in range(count):
        prefix=f'question_{index}_'
        for name in ('id','label','type','required','option'):allowed.add(prefix+name)
        if form.get(prefix+'required') not in ('0','1'):
            raise ValueError('Defina se a pergunta é obrigatória.')
        for name in ('id','label','type','required'):
            if len(form.getlist(prefix+name))!=1:raise ValueError('Confira os campos de cada pergunta.')
        questions.append(dict(id=form.get(prefix+'id',''),label=form.get(prefix+'label',''),type=form.get(prefix+'type',''),required=form.get(prefix+'required')=='1',options=form.getlist(prefix+'option')))
    if set(form)-allowed:raise ValueError('O editor contém campos desconhecidos. Recarregue a página.')
    return validate_questions(questions)


def load_questions(con,version):
    rows=con.execute('SELECT id,field_key,label,kind,required FROM form_questions WHERE version_id=? ORDER BY position,id',(version,)).fetchall()
    result=[]
    for qid,key,label,kind,required in rows:
        options=[r[0] for r in con.execute('SELECT value FROM form_options WHERE question_id=? ORDER BY position',(qid,))]
        result.append(dict(id=key,db_id=qid,label=label,type=kind,required=bool(required),options=options))
    return result


def create_version(con,jid,questions,actor=None):
    version=con.execute('INSERT INTO job_form_versions(job_id,created_at,created_by) VALUES(?,?,?)',(jid,int(time.time()),actor)).lastrowid
    for position,q in enumerate(questions):
        qid=con.execute('INSERT INTO form_questions(version_id,field_key,label,kind,required,position) VALUES(?,?,?,?,?,?)',(version,q['id'],q['label'],q['type'],int(q['required']),position)).lastrowid
        for i,option in enumerate(q['options']):
            con.execute('INSERT INTO form_options(question_id,value,position) VALUES(?,?,?)',(qid,option,i))
    return version


def current_form(con,j):
    # A single writer chooses the initial version; GET never creates an application.
    row=con.execute('SELECT current_form_version FROM jobs WHERE id=?',(j['id'],)).fetchone()
    if row and row[0]:return row[0],load_questions(con,row[0])
    owns_transaction=not con.in_transaction
    if owns_transaction:con.execute('BEGIN IMMEDIATE')
    row=con.execute('SELECT current_form_version FROM jobs WHERE id=?',(j['id'],)).fetchone()
    version=row[0]
    if not version:
        version=create_version(con,j['id'],defaults(j['side']))
        con.execute('UPDATE jobs SET current_form_version=? WHERE id=?',(version,j['id']))
    if owns_transaction:con.commit()
    return version,load_questions(con,version)


def read_answers(con,application_id,questions):
    answers={q['id']:[] if q['type']=='multiselect' else '' for q in questions}
    for key,kind,value in con.execute('SELECT q.field_key,q.kind,a.value FROM application_answers a JOIN form_questions q ON q.id=a.question_id WHERE a.application_id=? ORDER BY a.position',(application_id,)):
        if kind=='multiselect':answers.setdefault(key,[]).append(value)
        else:answers[key]=value
    return answers


def write_answers(con,application_id,questions,answers):
    con.execute('DELETE FROM application_answers WHERE application_id=?',(application_id,))
    for q in questions:
        value=answers.get(q['id'],[] if q['type']=='multiselect' else '')
        values=value if isinstance(value,list) else [value]
        for position,item in enumerate(values):
            con.execute('INSERT INTO application_answers(application_id,question_id,position,value) VALUES(?,?,?,?)',(application_id,q['db_id'],position,item))


def migrate(con):
    cols={r[1] for r in con.execute('PRAGMA table_info(applications)')}
    for name,definition in [('status',"TEXT NOT NULL DEFAULT 'submitted'"),('form_version','INTEGER'),('updated_at','INTEGER'),('submitted_at','INTEGER'),('feedback',"TEXT NOT NULL DEFAULT ''"),('notes',"TEXT NOT NULL DEFAULT ''")]:
        if name not in cols:con.execute(f'ALTER TABLE applications ADD COLUMN {name} {definition}')
    con.execute('CREATE TABLE IF NOT EXISTS recruitment_migrations(name TEXT PRIMARY KEY)')
    legacy_columns={r[1] for r in con.execute('PRAGMA table_info(job_form_versions)')}
    if 'questions_json' in legacy_columns:
        con.execute('ALTER TABLE job_form_versions RENAME TO legacy_job_form_versions')
    con.execute('CREATE TABLE IF NOT EXISTS job_form_versions(id INTEGER PRIMARY KEY,job_id INTEGER NOT NULL REFERENCES jobs(id),created_at INTEGER NOT NULL,created_by INTEGER REFERENCES users(id))')
    if 'current_form_version' not in {r[1] for r in con.execute('PRAGMA table_info(jobs)')}:
        con.execute('ALTER TABLE jobs ADD COLUMN current_form_version INTEGER REFERENCES job_form_versions(id)')
    con.execute('CREATE INDEX IF NOT EXISTS idx_job_form_versions_relational ON job_form_versions(job_id,id)')
    con.execute('CREATE TABLE IF NOT EXISTS form_questions(id INTEGER PRIMARY KEY,version_id INTEGER NOT NULL REFERENCES job_form_versions(id),field_key TEXT NOT NULL,label TEXT NOT NULL,kind TEXT NOT NULL,required INTEGER NOT NULL CHECK(required IN(0,1)),position INTEGER NOT NULL,UNIQUE(version_id,field_key))')
    con.execute('CREATE TABLE IF NOT EXISTS form_options(question_id INTEGER NOT NULL REFERENCES form_questions(id),value TEXT NOT NULL,position INTEGER NOT NULL,PRIMARY KEY(question_id,position),UNIQUE(question_id,value))')
    con.execute('CREATE TABLE IF NOT EXISTS application_answers(application_id INTEGER NOT NULL REFERENCES applications(id),question_id INTEGER NOT NULL REFERENCES form_questions(id),position INTEGER NOT NULL,value TEXT NOT NULL,PRIMARY KEY(application_id,question_id,position))')
    con.execute('CREATE TABLE IF NOT EXISTS application_history(id INTEGER PRIMARY KEY,application_id INTEGER NOT NULL REFERENCES applications(id),actor_id INTEGER NOT NULL REFERENCES users(id),status TEXT NOT NULL,created_at INTEGER NOT NULL)')
    if not con.execute("SELECT 1 FROM recruitment_migrations WHERE name='relational_forms_v1'").fetchone():
        _migrate_legacy(con,cols)
        con.execute("INSERT INTO recruitment_migrations(name) VALUES('relational_forms_v1')")
    con.execute('UPDATE applications SET submitted_at=created_at WHERE submitted_at IS NULL AND status!=?',('draft',))
    for jid,side in con.execute('SELECT id,side FROM jobs').fetchall():current_form(con,dict(id=jid,side=side))


def _migrate_legacy(con,application_columns):
    # JSON is read only here, to preserve data from the previous local schema.
    legacy=con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='legacy_job_form_versions'").fetchone()
    versions={}
    if legacy:
        for old_id,jid,raw,created,actor in con.execute('SELECT id,job_id,questions_json,created_at,created_by FROM legacy_job_form_versions ORDER BY id').fetchall():
            questions=validate_questions(json.loads(raw))
            version=create_version(con,jid,questions,actor)
            con.execute('UPDATE job_form_versions SET created_at=? WHERE id=?',(created,version))
            versions[old_id]=version
            con.execute('UPDATE jobs SET current_form_version=? WHERE id=?',(version,jid))
    app_rows=con.execute('SELECT id,job_id,form_version FROM applications').fetchall()
    for aid,jid,old_version in app_rows:
        questions=None
        if 'questions_snapshot' in application_columns:
            raw=con.execute('SELECT questions_snapshot FROM applications WHERE id=?',(aid,)).fetchone()[0]
            snapshot=json.loads(raw or '[]')
            if snapshot:questions=validate_questions(snapshot)
        if questions:
            version=create_version(con,jid,questions)
        elif old_version in versions:
            version=versions[old_version]
        else:
            j=con.execute('SELECT side FROM jobs WHERE id=?',(jid,)).fetchone()
            if not j:raise ValueError('Candidatura legada aponta para vaga inexistente.')
            version=create_version(con,jid,defaults(j[0]))
        con.execute('UPDATE applications SET form_version=? WHERE id=?',(version,aid))
        if 'answers_json' in application_columns:
            raw=con.execute('SELECT answers_json FROM applications WHERE id=?',(aid,)).fetchone()[0]
            answers=json.loads(raw or '{}')
            write_answers(con,aid,load_questions(con,version),answers)


def register_routes(app,db,login_required,mentor_required):
    app.context_processor(lambda:dict(recruitment_statuses=STATUSES))
    def form_signer():
        return TimestampSigner(app.secret_key,salt='recruitment-form-version-v2')
    def job(jid):
        row=db().execute('SELECT * FROM jobs WHERE id=?',(jid,)).fetchone()
        if not row:abort(404)
        return vacancies.decorate(row)
    def latest(j):
        return current_form(db(),j)
    def own(jid):
        row=db().execute('SELECT * FROM applications WHERE job_id=? AND user_id=?',(jid,session['user_id'])).fetchone()
        return dict(row) if row else None
    def context(jid):
        j=job(jid);a=own(jid)
        if not a and vacancies.state(j) in ('draft','paused'):abort(404)
        version,qs=latest(j)
        if a:
            version=a['form_version']
            qs=load_questions(db(),version)
            answers=read_answers(db(),a['id'],qs)
        else:answers={}
        return j,a,version,qs,answers
    def validate(qs,complete):
        allowed={'csrf_token','form_token','action'}|{'q_'+q['id'] for q in qs}
        errors={};answers={}
        if set(request.form)-allowed:errors['_form']='O formulário contém campos desconhecidos. Recarregue a página.'
        for q in qs:
            key=q['id'];values=request.form.getlist('q_'+key)
            if q['type']=='multiselect':
                value=list(dict.fromkeys(values))
                if any(v not in q['options'] for v in value):errors[key]='Escolha somente as opções disponíveis.'
            else:
                value=(values[0] if values else '').strip()
                if len(values)>1:errors[key]='Informe apenas um valor.'
                if len(value)>(6000 if q['type']=='textarea' else 1000):errors[key]='Resposta muito longa.'
                if value and q['type']=='select' and value not in q['options']:errors[key]='Escolha uma opção disponível.'
                if value and q['type']=='number' and not re.fullmatch(r'-?\d{1,10}(?:\.\d{1,4})?',value):errors[key]='Informe um número válido.'
                if value and q['type']=='url':
                    try:
                        parts=urlsplit(value)
                        port=parts.port
                        valid=parts.scheme in ('http','https') and bool(parts.hostname) and not parts.username and not parts.password and not any(c.isspace() for c in value)
                        if not valid:raise ValueError()
                    except ValueError:
                        errors[key]='Informe uma URL http ou https válida.'
            if complete and q['required'] and not value:errors[key]='Responda a esta pergunta para continuar.'
            answers[key]=value
        return answers,errors
    def participant():
        if session.get('role')!='participante':abort(403)

    @app.get('/opportunities')
    def opportunities():
        rows=db().execute('SELECT * FROM jobs WHERE active=1 ORDER BY id DESC').fetchall()
        return render_template('opportunities.html',jobs=[vacancies.decorate(r) for r in rows if vacancies.is_open(r)])

    @app.get('/opportunities/<int:jid>')
    def opportunity(jid):
        j=job(jid)
        if vacancies.state(j) in ('draft','paused'):abort(404)
        return render_template('opportunity.html',job=j)

    @app.route('/applications/<int:jid>/form',methods=['GET','POST'])
    @login_required
    def application_form(jid):
        participant();j,a,version,qs,answers=context(jid);errors={}
        if a and a['status']!='draft':return redirect('/my-applications')
        if request.method=='POST':
            try:
                raw=form_signer().unsign(request.form.get('form_token',''),max_age=8*60*60).decode('utf-8')
                signed_job,signed_user,version=map(int,raw.split(':'))
                if signed_job!=jid or signed_user!=session['user_id']:
                    raise ValueError()
                if not db().execute('SELECT 1 FROM job_form_versions WHERE id=? AND job_id=?',(version,jid)).fetchone():
                    raise ValueError()
                if a and version!=a['form_version']:
                    raise ValueError()
                qs=load_questions(db(),version)
            except (BadSignature,ValueError,KeyError,TypeError):
                abort(400,description='O formulário expirou ou mudou de contexto. Recarregue a página antes de continuar.')
            action=request.form.get('action')
            if action not in ('save','review'):abort(400)
            answers,errors=validate(qs,action=='review')
            if not vacancies.is_open(j):errors['_form']='Esta vaga não está recebendo inscrições. Suas respostas anteriores foram preservadas.'
            if not errors:
                d=db();d.execute('BEGIN IMMEDIATE')
                if not vacancies.is_open(d.execute('SELECT * FROM jobs WHERE id=?',(jid,)).fetchone()):abort(400,description='A vaga não está recebendo inscrições.')
                existing=d.execute('SELECT status,form_version FROM applications WHERE job_id=? AND user_id=?',(jid,session['user_id'])).fetchone()
                if existing and existing['status']!='draft':
                    d.rollback()
                    return redirect('/my-applications')
                if existing and existing['form_version']!=version:
                    abort(400,description='O rascunho foi atualizado em outra sessão. Recarregue o formulário antes de continuar.')
                now=int(time.time())
                d.execute("INSERT OR IGNORE INTO applications(job_id,user_id,created_at,status,form_version,updated_at) VALUES(?,?,?,'draft',?,?)",(jid,session['user_id'],now,version,now))
                application_id=d.execute('SELECT id FROM applications WHERE job_id=? AND user_id=?',(jid,session['user_id'])).fetchone()[0]
                write_answers(d,application_id,qs,answers)
                d.execute("UPDATE applications SET updated_at=? WHERE id=?",(now,application_id))
                d.commit()
                flash('Rascunho salvo.')
                return redirect(f'/applications/{jid}/review' if action=='review' else f'/applications/{jid}/form')
        form_token=form_signer().sign(f"{jid}:{session['user_id']}:{version}").decode('utf-8')
        return render_template('application_form.html',job=j,questions=qs,answers=answers,application=a,errors=errors,form_token=form_token),400 if errors else 200

    @app.route('/applications/<int:jid>/review',methods=['GET','POST'])
    @login_required
    def application_review(jid):
        participant();j,a,version,qs,answers=context(jid)
        if not a:return redirect(f'/applications/{jid}/form')
        if a['status']!='draft':return redirect('/my-applications')
        if any(q['required'] and not answers.get(q['id']) for q in qs):return redirect(f'/applications/{jid}/form')
        if request.method=='POST':
            d=db();d.execute('BEGIN IMMEDIATE')
            if not vacancies.is_open(d.execute('SELECT * FROM jobs WHERE id=?',(jid,)).fetchone()):abort(400,description='As inscrições estão encerradas ou pausadas. Seu rascunho foi preservado.')
            current=d.execute('SELECT status,form_version FROM applications WHERE id=? AND user_id=?',(a['id'],session['user_id'])).fetchone()
            current_questions=load_questions(d,current['form_version'])
            current_answers=read_answers(d,a['id'],current_questions)
            if current['status']=='draft' and any(q['required'] and not current_answers.get(q['id']) for q in current_questions):
                abort(400,description='O rascunho mudou e está incompleto. Revise o formulário antes de enviar.')
            now=int(time.time())
            result=d.execute("UPDATE applications SET status='submitted',submitted_at=?,updated_at=? WHERE id=? AND user_id=? AND status='draft'",(now,now,a['id'],session['user_id']))
            if result.rowcount:d.execute('INSERT INTO application_history(application_id,actor_id,status,created_at) VALUES(?,?,?,?)',(a['id'],session['user_id'],'submitted',now))
            d.commit();flash('Candidatura enviada. Acompanhe as próximas etapas aqui.');return redirect('/my-applications')
        return render_template('application_review.html',job=j,questions=qs,answers=answers,application=a)

    @app.get('/my-applications')
    @login_required
    def my_applications():
        participant()
        # Notas internas nunca são carregadas nesta consulta.
        rows=db().execute('SELECT a.id,a.job_id,a.status,a.created_at,a.updated_at,a.feedback,j.title job_title,j.company FROM applications a JOIN jobs j ON j.id=a.job_id WHERE a.user_id=? ORDER BY a.id DESC',(session['user_id'],)).fetchall()
        return render_template('my_applications.html',applications=[dict(r) for r in rows])

    @app.get('/admin')
    @mentor_required
    def recruitment_admin():
        q=request.args.get('q','').strip()
        selected_status=request.args.get('status','')
        job_id=request.args.get('job_id','')
        raw_page=request.args.get('page','1')
        if len(q)>120 or (selected_status and (selected_status not in STATUSES or selected_status=='draft')):
            abort(400,description='Confira a busca e a etapa informada.')
        if not re.fullmatch(r'[0-9]{1,9}',raw_page) or int(raw_page)<1:
            abort(400,description='Informe uma página válida.')
        if job_id and (not re.fullmatch(r'[0-9]{1,18}',job_id) or int(job_id)<1):
            abort(400,description='Informe uma vaga válida.')
        page=int(raw_page);per_page=20
        rows=[vacancies.decorate(r) for r in db().execute("SELECT j.*, (SELECT COUNT(*) FROM applications a WHERE a.job_id=j.id AND a.status!='draft') applicant_count FROM jobs j ORDER BY j.id DESC")]
        for item in rows:item['application_count']=item['applicant_count']
        base=" FROM applications a JOIN users u ON u.id=a.user_id JOIN jobs j ON j.id=a.job_id WHERE a.status!='draft'"
        conditions=[];params=[]
        if q:
            # Busca literal: % e _ digitados não viram coringas SQL.
            term='%'+q.replace('!', '!!').replace('%','!%').replace('_','!_')+'%'
            conditions.append("(u.name LIKE ? ESCAPE '!' OR j.title LIKE ? ESCAPE '!')");params.extend([term,term])
        if selected_status:conditions.append('a.status=?');params.append(selected_status)
        if job_id:conditions.append('a.job_id=?');params.append(int(job_id))
        filtered=base+(' AND '+' AND '.join(conditions) if conditions else '')
        total=db().execute('SELECT COUNT(*)'+filtered,params).fetchone()[0]
        pages=max(1,(total+per_page-1)//per_page);page=min(page,pages)
        applications=[dict(r) for r in db().execute('SELECT a.id,a.job_id,a.status,u.name,j.title job_title'+filtered+' ORDER BY a.id DESC LIMIT ? OFFSET ?',params+[per_page,(page-1)*per_page])]
        stats=dict(jobs=len(rows),applications=db().execute('SELECT COUNT(*)'+base).fetchone()[0],drafts=db().execute("SELECT COUNT(*) FROM applications WHERE status='draft'").fetchone()[0])
        return render_template('admin.html',jobs=rows,applications=applications,stats=stats,
            filters=dict(q=q,status=selected_status,job_id=job_id),
            pagination=dict(page=page,pages=pages,total=total,per_page=per_page))

    @app.route('/admin/jobs/<int:jid>/form',methods=['GET','POST'])
    @mentor_required
    def admin_job_form(jid):
        j=job(jid);version,qs=latest(j);errors={}
        if request.method=='POST':
            try:questions=parse_editor(request.form)
            except ValueError as exc:
                errors['questions']=str(exc)
                try:count=min(15,max(0,int(request.form.get('question_count','0'))))
                except ValueError:count=0
                if count:
                    qs=[dict(id=request.form.get(f'question_{i}_id','')[:40],label=request.form.get(f'question_{i}_label','')[:200],type=request.form.get(f'question_{i}_type','text'),required=request.form.get(f'question_{i}_required')=='1',options=request.form.getlist(f'question_{i}_option')[:21]) for i in range(count)]
            if not errors:
                d=db();d.execute('BEGIN IMMEDIATE')
                version=create_version(d,jid,questions,session['user_id'])
                d.execute('UPDATE jobs SET current_form_version=? WHERE id=?',(version,jid))
                d.commit();flash('Nova versão do formulário salva. Inscrições existentes foram preservadas.');return redirect('/admin')
        return render_template('admin_job_form.html',job=j,questions=qs,errors=errors),400 if errors else 200

    @app.route('/admin/applications/<int:aid>',methods=['GET','POST'])
    @mentor_required
    def admin_application(aid):
        row=db().execute("SELECT a.*,u.name,u.email,j.title job_title FROM applications a JOIN users u ON u.id=a.user_id JOIN jobs j ON j.id=a.job_id WHERE a.id=? AND a.status!='draft'",(aid,)).fetchone()
        if not row:abort(404)
        a=dict(row)
        if request.method=='POST':
            status=request.form.get('status','');feedback=request.form.get('feedback','').strip();notes=request.form.get('notes','').strip()
            if status not in STATUSES or status=='draft' or len(feedback)>4000 or len(notes)>4000:abort(400,description='Confira a etapa e limite cada parecer a 4000 caracteres.')
            now=int(time.time());d=db();d.execute('BEGIN IMMEDIATE')
            old_status=d.execute('SELECT status FROM applications WHERE id=?',(aid,)).fetchone()[0]
            d.execute('UPDATE applications SET status=?,feedback=?,notes=?,updated_at=? WHERE id=?',(status,feedback,notes,now,aid))
            if status!=old_status:d.execute('INSERT INTO application_history(application_id,actor_id,status,created_at) VALUES(?,?,?,?)',(aid,session['user_id'],status,now))
            d.commit();flash('Parecer salvo. Somente o feedback compartilhável será apresentado ao candidato.');return redirect(f'/admin/applications/{aid}')
        qs=load_questions(db(),a['form_version']);answers=read_answers(db(),aid,qs);a.update(questions=qs,answers=answers)
        history=[]
        for event in db().execute('''SELECT h.id,h.status,h.created_at,h.actor_id,
                COALESCE(NULLIF(u.name,''),'Usuário indisponível') actor_name
                FROM application_history h LEFT JOIN users u ON u.id=h.actor_id
                WHERE h.application_id=? ORDER BY h.created_at,h.id''',(aid,)):
            item=dict(event)
            try:
                instant=datetime(1970,1,1,tzinfo=timezone.utc)+timedelta(seconds=item['created_at'])
                item.update(created_at_label=instant.strftime('%d/%m/%Y %H:%M UTC'),created_at_iso=instant.isoformat())
            except (TypeError, ValueError, OverflowError):
                item.update(created_at_label='Data indisponível',created_at_iso='')
            history.append(item)
        return render_template('admin_application.html',application=a,questions=qs,answers=answers,history=history)
