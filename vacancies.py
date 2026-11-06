"""Ciclo editorial das vagas e prazo de inscrições, sem excluir candidaturas."""
import time
from datetime import date, datetime, timedelta, timezone
from flask import abort, flash, redirect, render_template, request, session

STATES = {'draft':'Rascunho','published':'Publicada','paused':'Pausada','closed':'Encerrada'}
SENIORITIES = ('Estágio','Júnior','Pleno','Sênior')
MODALITIES = ('Remoto','Híbrido','Presencial')
BRASILIA = timezone(timedelta(hours=-3))


def migrate(con):
    columns={r[1] for r in con.execute('PRAGMA table_info(jobs)')}
    additions={'status':"TEXT NOT NULL DEFAULT 'published'",'deadline_at':'INTEGER','seniority':"TEXT NOT NULL DEFAULT ''",'modality':"TEXT NOT NULL DEFAULT ''",'location':"TEXT NOT NULL DEFAULT ''",'updated_at':'INTEGER','revision':'INTEGER NOT NULL DEFAULT 1'}
    for key,definition in additions.items():
        if key not in columns:con.execute(f'ALTER TABLE jobs ADD COLUMN {key} {definition}')
    if 'status' not in columns:con.execute("UPDATE jobs SET status=CASE WHEN active=1 THEN 'published' ELSE 'paused' END")
    con.execute('CREATE INDEX IF NOT EXISTS idx_jobs_editorial ON jobs(status,active,deadline_at)')
    con.execute('CREATE TABLE IF NOT EXISTS job_history(id INTEGER PRIMARY KEY,job_id INTEGER NOT NULL REFERENCES jobs(id),actor_id INTEGER REFERENCES users(id),event TEXT NOT NULL,from_state TEXT,to_state TEXT NOT NULL,revision INTEGER NOT NULL,created_at INTEGER NOT NULL)')


def state(job):
    job=dict(job)
    value=job.get('status','published')
    return 'paused' if value=='published' and not job.get('active',1) else value


def is_open(job,now=None):
    job=dict(job);now=int(time.time()) if now is None else now
    return state(job)=='published' and bool(job.get('active',1)) and (job.get('deadline_at') is None or job['deadline_at']>now)


def deadline_value(value):
    return (datetime(1970,1,1,tzinfo=timezone.utc)+timedelta(seconds=value)-timedelta(seconds=1)).astimezone(BRASILIA).date().isoformat() if value else ''


def deadline_label(job):
    value=dict(job).get('deadline_at')
    return (datetime(1970,1,1,tzinfo=timezone.utc)+timedelta(seconds=value)-timedelta(seconds=1)).astimezone(BRASILIA).strftime('%d/%m/%Y') if value else 'Sem prazo definido'


def state_label(job):
    return 'Prazo encerrado' if state(job)=='published' and not is_open(job) else STATES.get(state(job),'Indisponível')


def decorate(job):
    item=dict(job);item.update(is_open=is_open(item),deadline_display=deadline_label(item),status=state(item))
    return item


def event(con,jid,actor,kind,old,new,revision):
    con.execute('INSERT INTO job_history(job_id,actor_id,event,from_state,to_state,revision,created_at) VALUES(?,?,?,?,?,?,?)',(jid,actor,kind,old,new,revision,int(time.time())))


def read_values(form):
    keys=('title','company','description','side','min_points','seniority','modality','location','deadline','revision')
    return {key:form.get(key,'').strip() for key in keys}


def validate(values,target):
    errors={};clean=dict(values)
    if not 3<=len(values['title'])<=120:errors['title']='Informe um título entre 3 e 120 caracteres.'
    if len(values['company'])>120 or (target!='draft' and len(values['company'])<2):errors['company']='Informe a empresa, com 2 a 120 caracteres, para publicar.'
    if len(values['description'])>4000 or (target!='draft' and len(values['description'])<10):errors['description']='Descreva a oportunidade em 10 a 4000 caracteres para publicar.'
    if values['side'] not in ('Red Team','Blue Team','Purple Team'):errors['side']='Escolha uma área válida.'
    for key,options in [('seniority',SENIORITIES),('modality',MODALITIES)]:
        if values[key] not in ('',*options):errors[key]='Escolha uma opção válida.'
    if len(values['location'])>120:errors['location']='Limite o local a 120 caracteres.'
    try:
        clean['min_points']=int(values['min_points'] or '0')
        if not 0<=clean['min_points']<=100000:raise ValueError()
    except ValueError:errors['min_points']='Informe pontos entre 0 e 100000.'
    clean['deadline_at']=None
    if values['deadline']:
        try:
            selected=date.fromisoformat(values['deadline'])
            if selected.isoformat()!=values['deadline'] or not 2000<=selected.year<=2100:raise ValueError()
            clean['deadline_at']=int(datetime.combine(selected+timedelta(days=1),datetime.min.time(),BRASILIA).timestamp())
        except (ValueError,OverflowError):errors['deadline']='Informe uma data válida entre os anos 2000 e 2100.'
    if target=='published' and clean['deadline_at'] is not None and clean['deadline_at']<=int(time.time()):errors['deadline']='A publicação precisa de um prazo ainda aberto.'
    return clean,errors


def register_routes(app,db,mentor_required):
    app.context_processor(lambda:dict(job_states=STATES,job_is_open=is_open,job_state_label=state_label,job_deadline=deadline_label,seniorities=SENIORITIES,modalities=MODALITIES))
    def find(jid):
        row=db().execute('SELECT * FROM jobs WHERE id=?',(jid,)).fetchone()
        if not row:abort(404)
        return dict(row)
    def editor(jid=None):
        job=find(jid) if jid else None
        values={key:str(job.get(key) or '') for key in ('title','company','description','side','min_points','seniority','modality','location','revision')} if job else dict(title='',company='',description='',side='Purple Team',min_points='0',seniority='',modality='',location='',revision='')
        values['deadline']=deadline_value(job.get('deadline_at')) if job else ''
        errors={};code=200
        if request.method=='POST':
            values=read_values(request.form);action=request.form.get('action','')
            if action not in ('save_draft','publish','save'):abort(400)
            old=state(job) if job else None
            target='published' if action=='publish' else 'draft' if action=='save_draft' or not job else old
            if old=='closed' and target!='closed':errors['_form']='Uma vaga encerrada não pode ser reaberta. Cadastre outra oportunidade.'
            if old and old!='draft' and target=='draft':errors['_form']='Uma vaga já publicada não volta a rascunho. Use pausar ou encerrar.'
            clean,invalid=validate(values,target);errors.update(invalid)
            if job:
                try:revision=int(values['revision'])
                except ValueError:revision=-1
                if revision!=job['revision']:errors['_form']='A vaga foi alterada em outra sessão. Recarregue antes de salvar.';code=409
            if not errors:
                d=db();d.execute('BEGIN IMMEDIATE')
                if job:
                    current=find(jid)
                    if current['revision']!=revision:
                        d.rollback();errors['_form']='A vaga foi alterada em outra sessão. Recarregue antes de salvar.';code=409
                    elif clean['side']!=current['side'] and d.execute('SELECT 1 FROM applications WHERE job_id=? LIMIT 1',(jid,)).fetchone():
                        d.rollback();errors['side']='A área não pode mudar após o início de candidaturas; crie outra vaga.'
                    else:
                        new_revision=revision+1
                        d.execute('UPDATE jobs SET title=?,company=?,description=?,side=?,min_points=?,seniority=?,modality=?,location=?,deadline_at=?,status=?,active=?,revision=?,updated_at=? WHERE id=?',(clean['title'],clean['company'],clean['description'],clean['side'],clean['min_points'],clean['seniority'],clean['modality'],clean['location'],clean['deadline_at'],target,int(target=='published'),new_revision,int(time.time()),jid))
                        event(d,jid,session['user_id'],'edited',old,target,new_revision);d.commit()
                else:
                    jid=d.execute('INSERT INTO jobs(title,company,description,side,min_points,seniority,modality,location,deadline_at,status,active,revision,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,1,?,?,?)',(clean['title'],clean['company'],clean['description'],clean['side'],clean['min_points'],clean['seniority'],clean['modality'],clean['location'],clean['deadline_at'],target,int(target=='published'),session['user_id'],int(time.time()),int(time.time()))).lastrowid
                    event(d,jid,session['user_id'],'created',None,target,1);d.commit()
                if not errors:flash('Vaga publicada.' if target=='published' else 'Vaga salva.');return redirect(f'/admin/jobs/{jid}/edit')
            if errors and code==200:code=400
        return render_template('vacancy_editor.html',values=values,errors=errors,job=decorate(job) if job else None,is_conflict=code==409),code

    @app.route('/admin/jobs/new',methods=['GET','POST'])
    @mentor_required
    def vacancy_new():return editor()

    @app.route('/admin/jobs/<int:jid>/edit',methods=['GET','POST'])
    @mentor_required
    def vacancy_edit(jid):return editor(jid)

    @app.post('/admin/jobs/<int:jid>/state')
    @mentor_required
    def vacancy_state(jid):
        target=request.form.get('state','')
        if target not in STATES:abort(400)
        try:revision=int(request.form.get('revision',''))
        except ValueError:abort(400,description='Recarregue a vaga antes de alterar o estado.')
        d=db();d.execute('BEGIN IMMEDIATE');job=find(jid);old=state(job)
        if old==target:
            d.rollback();return redirect(f'/admin/jobs/{jid}/edit')
        if revision!=job['revision']:
            d.rollback();abort(409,description='A vaga foi alterada em outra sessão. Recarregue antes de continuar.')
        allowed={'draft':{'published'},'published':{'paused','closed'},'paused':{'published','closed'},'closed':set()}
        if target not in allowed.get(old,set()):abort(400,description='Essa transição não está disponível. Uma vaga encerrada permanece preservada.')
        if target=='published':
            values={key:str(job.get(key) or '') for key in ('title','company','description','side','min_points','seniority','modality','location','revision')};values['deadline']=deadline_value(job.get('deadline_at'))
            _,errors=validate(values,target)
            if errors:abort(400,description='Complete os dados da vaga e confira o prazo antes de publicar.')
        d.execute('UPDATE jobs SET status=?,active=?,revision=revision+1,updated_at=? WHERE id=?',(target,int(target=='published'),int(time.time()),jid))
        event(d,jid,session['user_id'],'state_changed',old,target,revision+1);d.commit()
        flash('Estado da vaga atualizado. Candidaturas existentes foram preservadas.');return redirect(f'/admin/jobs/{jid}/edit')

    @app.get('/admin/jobs/<int:jid>/preview')
    @mentor_required
    def vacancy_preview(jid):return render_template('opportunity.html',job=decorate(find(jid)),preview=True)
