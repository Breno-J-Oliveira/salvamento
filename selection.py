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
    # Cada candidatura armazena os briefings que recebeu; alterar esta função
    # não reescreve as evidências de avaliações já iniciadas.
    if side == 'Red Team':
        return [
            dict(title='Investigar o dossiê AppSec', briefing="""DOSSIÊ APPSEC / v2 · ambiente fictício autorizado
Janela: 10:00–10:15 UTC. Dados de teste; não há alvo externo autorizado.

CONTAS E DADOS
conta A: perfil cliente, pedido 41, tenant alfa
conta B: perfil cliente, pedido 42, tenant beta
conta S: suporte, sem delegação para beta

CAPTURA HTTP
10:01 req-101 conta=A GET /api/orders/41 -> 200 {owner:A, tenant:alfa, total:120}
10:02 req-102 conta=A GET /api/orders/42 -> 200 {owner:B, tenant:beta, total:380}
10:03 req-103 conta=B GET /api/orders/41 -> 404
10:04 req-104 conta=A GET /api/orders/999 -> 404
10:05 req-105 conta=S GET /api/orders/42 -> 403
10:06 req-106 anônimo GET /api/orders/42 -> 401

EVENTOS DA APLICAÇÃO
req-102 handler=orders.get cache=HIT cache_key=order:42
req-103 handler=orders.get cache=MISS policy=deny
req-105 handler=orders.get cache=MISS policy=deny

Documente fatos, hipóteses concorrentes, impacto possível e limites da evidência. Que verificações controladas diferenciariam as hipóteses? Cite os identificadores usados."""),
            dict(title='Projetar a verificação', briefing="""CONTEXTO ADICIONAL / AppSec v2
A equipe informa que a falha não foi reproduzida em uma instância recém-iniciada. A captura veio de um único nó. Ainda não há rastreamento do preenchimento do cache nem configuração do gateway.

Entregue uma matriz de testes positivos e negativos com identidades, recursos, estado inicial e resultado esperado. Defina como preservar evidências e evitar exposição de dados. Explique quais conclusões continuam condicionais e quais achados justificam escalonamento."""),
            dict(title='Entregar parecer técnico', briefing="""PARECER / AppSec v2
A empresa precisa decidir se mantém o endpoint disponível enquanto investiga. O serviço é usado por clientes e pelo suporte; uma interrupção tem impacto operacional.

Apresente sua decisão, alternativas, medidas imediatas e critérios de validação. Descreva como comprovar a correção, monitorar recorrência e comunicar impacto à equipe responsável. Diferencie evidência confirmada, risco estimado e informação ainda ausente.""")]
    return [
        dict(title='Investigar o dossiê SOC', briefing="""DOSSIÊ SOC / v2 · captura sintética
Janela: 09:00–09:15 UTC. Endereços reservados para documentação.

AUTENTICAÇÃO
09:00 auth-01 user=deploy src=192.0.2.18 result=failed
09:01 auth-02 user=deploy src=192.0.2.18 result=failed
09:02 auth-03 user=deploy src=192.0.2.18 result=success session=s-71 mfa=not_enrolled
09:02 auth-04 user=ana src=203.0.113.34 result=success session=s-72 mfa=passed
09:03 auth-05 user=backup src=198.51.100.10 result=success session=s-73

APLICAÇÃO
09:03 req-71 session=s-71 GET /reports/export result=200 rows=5000
09:04 req-72 session=s-72 GET /reports result=200 rows=20
09:05 req-73 session=s-73 POST /backup result=202 job=b-19
09:06 req-74 session=s-71 GET /reports/export result=200 rows=5000
09:07 req-75 session=s-71 GET /admin/users result=403

OPERAÇÃO
CHG-104: backup previsto 09:00–09:30, conta=backup
Cadastro deploy: origem habitual 198.51.100.10, janela habitual 13:00–18:00
Alerta e-18: CPU acima de 80% às 09:05

Documente a linha do tempo e priorize o que precisa ser investigado. Apresente hipóteses concorrentes e cite os registros que sustentam ou limitam cada uma. Não presuma que um alerta, sozinho, prova comprometimento."""),
        dict(title='Correlacionar e decidir', briefing="""EVIDÊNCIAS ADICIONAIS / SOC v2
09:05 process p-19 parent=backup-agent action=compress job=b-19
09:06 network n-21 service=web bytes_out=8400000 request=req-74
09:08 monitor e-22 disk_latency=high host=storage-02
09:09 backup b-19 state=completed checksum=ok
09:10 chamado OPS-208: o responsável por deploy ainda não foi contatado
Ausentes: conteúdo exportado, origem da credencial e resultado de validação com o responsável.

Correlacione as fontes e indique o que pode ser atribuído ao mesmo evento. Decida quais ações são proporcionais agora, quais exigem confirmação e qual informação mudaria sua decisão. Justifique prioridade, impacto e preservação de evidências."""),
        dict(title='Entregar relatório de incidente', briefing="""RELATÓRIO / SOC v2
A equipe solicita um parecer para decidir continuidade operacional, investigação e comunicação. Você dispõe apenas das capturas apresentadas.

Entregue: síntese executiva; achados com referências; hipóteses e confiança; ações em ordem de prioridade; riscos de cada ação; responsáveis a acionar; critérios para recuperação e encerramento. Declare expressamente os limites do seu parecer e as informações que ainda precisam ser verificadas.""")]


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
