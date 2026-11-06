"""Avaliação seletiva por candidatura, sem reutilizar pontos de prática livre."""
import json
import time
from flask import abort, flash, redirect, render_template, request, session

SCHEMA = """CREATE TABLE IF NOT EXISTS selection_assessments(
 application_id INTEGER PRIMARY KEY,started_at INTEGER NOT NULL,updated_at INTEGER NOT NULL,submitted_at INTEGER);
CREATE TABLE IF NOT EXISTS selection_stages(
 application_id INTEGER NOT NULL,position INTEGER NOT NULL,title TEXT NOT NULL,briefing TEXT NOT NULL,
 PRIMARY KEY(application_id,position),FOREIGN KEY(application_id) REFERENCES selection_assessments(application_id));
CREATE TABLE IF NOT EXISTS selection_responses(
 application_id INTEGER NOT NULL,position INTEGER NOT NULL,content TEXT NOT NULL,
 PRIMARY KEY(application_id,position),FOREIGN KEY(application_id,position) REFERENCES selection_stages(application_id,position));
"""

def migrate(connection):
    connection.executescript(SCHEMA)
    # Conversão incremental de snapshots antigos, sem remover informações originais.
    cols={r[1] for r in connection.execute('PRAGMA table_info(selection_assessments)')}
    if 'scenario_json' in cols:
        for aid,raw_questions,raw_responses in connection.execute('SELECT application_id,scenario_json,responses_json FROM selection_assessments').fetchall():
            if connection.execute('SELECT 1 FROM selection_stages WHERE application_id=?',(aid,)).fetchone():continue
            questions=json.loads(raw_questions or '[]');responses=json.loads(raw_responses or '{}')
            for position,q in enumerate(questions):
                connection.execute('INSERT INTO selection_stages VALUES(?,?,?,?)',(aid,position,q['title'],q['briefing']))
                if str(position) in responses:connection.execute('INSERT INTO selection_responses VALUES(?,?,?)',(aid,position,responses[str(position)]))


def stored_evidence(connection,aid):
    row=connection.execute('SELECT submitted_at FROM selection_assessments WHERE application_id=?',(aid,)).fetchone()
    if not row:return None
    return dict(questions=[dict(title=r[0],briefing=r[1]) for r in connection.execute('SELECT title,briefing FROM selection_stages WHERE application_id=? ORDER BY position',(aid,))],
                responses={str(r[0]):r[1] for r in connection.execute('SELECT position,content FROM selection_responses WHERE application_id=? ORDER BY position',(aid,))},submitted_at=row['submitted_at'])

def scenario(side):
    if side == 'Red Team':
        return [
            dict(title='Delimitar e investigar',briefing='Ambiente fictício autorizado: uma API recebe GET /orders/42 com sessão do usuário A e devolve pedido do usuário B. GET /orders/41 devolve pedido do usuário A. Não teste alvos externos. Descreva a hipótese, o escopo e as evidências necessárias para confirmar a falha de autorização.'),
            dict(title='Explicar o risco',briefing='O pedido contém endereço e itens comprados. O endpoint verifica se há sessão, mas consulta o pedido apenas pelo ID. Relacione o comportamento à causa, explique impacto e descreva um teste negativo sem acessar dados reais.'),
            dict(title='Corrigir e validar',briefing='Proponha autorização por proprietário e regras para acesso administrativo. Descreva como validar que o dono continua acessando o pedido e outros usuários recebem uma resposta segura. Registre limites e próximos passos.')]
    return [
        dict(title='Investigar autenticação',briefing='Cenário fictício SOC. 09:00 login failed user=deploy ip=192.0.2.18; 09:01 login failed user=deploy ip=192.0.2.18; 09:02 login success user=deploy ip=192.0.2.18. Horário habitual: 13h às 18h, origem esperada 198.51.100.10. Identifique a hipótese e evidências; explique por que esses dados ainda não provam comprometimento.'),
        dict(title='Correlacionar os eventos',briefing='09:03 a sessão de deploy iniciou uma exportação; 09:04 houve download de arquivo de teste; 09:05 o SIEM alertou sobre acesso fora do horário. Construa a linha do tempo, correlacione identidade e origem, e indique informações adicionais a consultar.'),
        dict(title='Conter e comunicar',briefing='A equipe confirmou que o responsável não reconhece a sessão. Proponha contenção proporcional, preservação de evidências, validação da recuperação e comunicação do incidente. Explique a ordem das ações e os riscos de bloquear uma conta de serviço.')]


def register_routes(app,db,login_required):
    def evidence(aid):
        return stored_evidence(db(),aid)
    app.context_processor(lambda:dict(selection_evidence=evidence))

    @app.route('/my-applications/<int:aid>/assessment',methods=['GET','POST'])
    @login_required
    def selection_assessment(aid):
        if session.get('role')!='participante':abort(403)
        d=db()
        row=d.execute('SELECT a.id,a.status,j.title,j.side FROM applications a JOIN jobs j ON j.id=a.job_id WHERE a.id=? AND a.user_id=?',(aid,session['user_id'])).fetchone()
        if not row:abort(404)
        if row['status'] not in ('submitted','review'):abort(403,description='Esta candidatura não está na etapa de avaliação prática.')
        assessment=d.execute('SELECT * FROM selection_assessments WHERE application_id=?',(aid,)).fetchone()
        data=stored_evidence(d,aid)
        questions=data['questions'] if data else scenario(row['side'])
        responses=data['responses'] if data else {}
        error=None
        if request.method=='POST':
            try:step=int(request.form.get('step',''))
            except ValueError:abort(400)
            response=request.form.get('response','').strip()
            if not 0<=step<len(questions):abort(400)
            if not 30<=len(response)<=6000:error='Descreva sua análise em 30 a 6000 caracteres.'
            if not error:
                d.execute('BEGIN IMMEDIATE')
                current=d.execute('SELECT status FROM applications WHERE id=? AND user_id=?',(aid,session['user_id'])).fetchone()
                if not current or current['status'] not in ('submitted','review'):abort(403)
                stored=d.execute('SELECT * FROM selection_assessments WHERE application_id=?',(aid,)).fetchone()
                if stored:
                    data=stored_evidence(d,aid);questions=data['questions'];responses=data['responses']
                    if stored['submitted_at']:
                        d.rollback();return redirect(request.path)
                if step!=len(responses):abort(400,description='Conclua as etapas na ordem apresentada.')
                responses[str(step)]=response
                now=int(time.time());finished=now if len(responses)==len(questions) else None
                if not stored:
                    cols={r[1] for r in d.execute('PRAGMA table_info(selection_assessments)')}
                    if 'scenario_json' in cols:
                        d.execute("INSERT INTO selection_assessments(application_id,scenario_json,responses_json,started_at,updated_at,submitted_at) VALUES(?,'','',?,?,?)",(aid,now,now,finished))
                    else:
                        d.execute('INSERT INTO selection_assessments(application_id,started_at,updated_at,submitted_at) VALUES(?,?,?,?)',(aid,now,now,finished))
                    for position,q in enumerate(questions):
                        d.execute('INSERT INTO selection_stages VALUES(?,?,?,?)',(aid,position,q['title'],q['briefing']))
                d.execute('INSERT INTO selection_responses VALUES(?,?,?)',(aid,step,response))
                d.execute('UPDATE selection_assessments SET updated_at=?,submitted_at=? WHERE application_id=?',(now,finished,aid))
                if finished:
                    d.execute("UPDATE applications SET status='review',updated_at=? WHERE id=?",(now,aid))
                    if current['status']!='review':d.execute("INSERT INTO application_history(application_id,actor_id,status,created_at) VALUES(?,?,?,?)",(aid,session['user_id'],'review',now))
                d.commit();flash('Avaliação enviada para revisão humana.' if finished else 'Etapa registrada. Continue sua investigação.')
                return redirect(request.path)
        return render_template('selection_assessment.html',application=dict(row),questions=questions,responses=responses,step=len(responses),finished=bool(assessment and assessment['submitted_at']),error=error),400 if error else 200
