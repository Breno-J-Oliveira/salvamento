"""Cria uma demonstração sintética em um arquivo novo; nunca lê o banco da equipe."""
import argparse
from contextlib import closing
import os
from pathlib import Path
import secrets
import sqlite3
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
DEMO_MARKER = 'purple-talent-presentation-v1'
CANDIDATE_EMAIL = 'candidato@demo.invalid'
CANDIDATE_PASSWORD = 'demonstracao123'  # Conta fictícia, exclusiva da demonstração local.


def prepare_demo(destination):
    destination = Path(destination).expanduser().absolute()
    # Rejeita links antes de resolver o caminho e nunca aceita o nome do banco operacional.
    if destination.name.lower() == 'lab.db' or destination.is_symlink():
        raise ValueError('Escolha um novo arquivo de demonstração, diferente de lab.db.')
    destination = destination.resolve()
    if destination.name.lower() == 'lab.db':
        raise ValueError('O destino não pode ser lab.db.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('xb'):
        pass
    try:
        # O import da aplicação não inicia servidor. A chave temporária evita criar/ler
        # .session-key para preparar fixtures; nenhuma credencial existente é alterada.
        previous_key = os.environ.get('SECRET_KEY')
        os.environ['SECRET_KEY'] = secrets.token_hex(32)
        sys.path.insert(0, str(ROOT))
        try:
            import app as application
        finally:
            if previous_key is None:
                os.environ.pop('SECRET_KEY', None)
            else:
                os.environ['SECRET_KEY'] = previous_key
        previous_db = application.DB
        try:
            application.DB = str(destination)
            application.init_db()
        finally:
            application.DB = previous_db
        _seed(destination)
        return destination
    except BaseException:
        # Somente o arquivo que esta chamada reservou, nunca um destino preexistente.
        destination.unlink(missing_ok=True)
        raise


def _seed(destination):
    import recruitment
    import selection
    from werkzeug.security import generate_password_hash

    now = int(time.time())
    with closing(sqlite3.connect(destination)) as connection:
        connection.execute('PRAGMA foreign_keys=ON')
        with connection:
            mentor = connection.execute("SELECT id FROM users WHERE role='mentor'").fetchone()[0]
            candidate = connection.execute(
                'INSERT INTO users(name,email,password,role,team) VALUES(?,?,?,?,?)',
                ('Alex Demo — pessoa fictícia', CANDIDATE_EMAIL,
                 generate_password_hash(CANDIDATE_PASSWORD), 'participante', 'Turma demonstração'),
            ).lastrowid
            jobs = []
            for title, side, seniority, modality in [
                ('DEMO — Analista SOC Júnior', 'Blue Team', 'Júnior', 'Híbrido'),
                ('DEMO — Estágio em AppSec', 'Red Team', 'Estágio', 'Remoto'),
            ]:
                description = (
                    'Vaga fictícia para apresentação do Purple Talent, sem processo real de contratação. '
                    'Investigue evidências sintéticas, explique hipóteses e comunique decisões. '
                    'A seleção inclui formulário e análise textual com revisão humana. '
                    'Conhecimentos introdutórios de redes e segurança são suficientes para esta demonstração.'
                )
                jid = connection.execute('''INSERT INTO jobs(title,company,description,side,min_points,
                    active,created_by,created_at,status,deadline_at,seniority,modality,location,updated_at)
                    VALUES(?,?,?,?,0,1,?,?,'published',?,?,?,?,?)''',
                    (title, 'Empresa fictícia de demonstração', description, side, mentor,
                     now - 86400, now + 30 * 86400, seniority, modality, 'São Paulo, SP', now),
                ).lastrowid
                questions = recruitment.defaults(side)
                questions.insert(1, dict(id='correlation', label='Qual campo ajuda a correlacionar duas requisições?',
                    type='select', required=True, options=['Request ID', 'Cor da página', 'Nome do navegador'],
                    correct_answer='Request ID'))
                version = recruitment.create_version(connection, jid, questions, mentor)
                connection.execute('UPDATE jobs SET current_form_version=? WHERE id=?', (version, jid))
                connection.execute('''INSERT INTO job_history(job_id,actor_id,event,from_state,to_state,revision,created_at)
                    VALUES(?,?,'created',NULL,'published',1,?)''', (jid, mentor, now - 86400))
                jobs.append((jid, version, side))

            for index, (jid, version, side) in enumerate(jobs):
                status = 'interview' if index == 0 else 'draft'
                feedback = ('Sua análise relacionou os registros e explicitou limites. '
                    'Na conversa de demonstração, explique como validaria a hipótese antes de conter o acesso. '
                    'Este retorno é fictício e não representa uma contratação.') if index == 0 else ''
                aid = connection.execute('''INSERT INTO applications(job_id,user_id,created_at,status,
                    form_version,updated_at,submitted_at,feedback,notes) VALUES(?,?,?,?,?,?,?,?,?)''',
                    (jid, candidate, now - 7200, status, version, now - 300,
                     now - 5400 if index == 0 else None, feedback,
                     'Nota interna sintética: explorar critérios de validação na entrevista.' if index == 0 else ''),
                ).lastrowid
                questions = recruitment.load_questions(connection, version)
                answers = dict(availability='20 horas semanais, período da tarde.',
                    correlation='Request ID' if index == 0 else '',
                    experience='Em um projeto didático, correlacionei autenticação e acesso usando identificadores e horários.',
                    portfolio='')
                recruitment.write_answers(connection, aid, questions, answers)
                events = [('draft', candidate, now - 7200)]
                if index == 0:
                    events += [('submitted', candidate, now - 5400), ('review', candidate, now - 3600),
                               ('interview', mentor, now - 300)]
                    connection.execute('INSERT INTO selection_assessments VALUES(?,?,?,?)',
                        (aid, now - 5000, now - 3600, now - 3600))
                    responses = [
                        'Exemplo fictício: auth-01 a auth-03 e req-71/req-74 justificam investigar a sessão s-71. O backup autorizado é uma hipótese concorrente distinta, sem prova isolada de comprometimento.',
                        'Exemplo fictício: correlacionaria n-21 com req-74, preservaria os registros e confirmaria a atividade com o responsável por deploy antes de definir uma contenção proporcional.',
                        'Exemplo fictício: os dados sustentam investigação prioritária, com confiança limitada. Faltam conteúdo exportado e validação com o responsável; registraria impacto, responsáveis e critérios de encerramento.',
                    ]
                    for position, (stage, response) in enumerate(zip(selection.scenario(side), responses)):
                        connection.execute('INSERT INTO selection_stages VALUES(?,?,?,?)',
                            (aid, position, stage['title'], stage['briefing']))
                        connection.execute('INSERT INTO selection_responses VALUES(?,?,?)',
                            (aid, position, response))
                    connection.execute('''INSERT INTO selection_reviews(application_id,revision,reviewer_id,
                        investigation,evidence,decisions,communication,justification,created_at)
                        VALUES(?,1,?,3,4,3,4,?,?)''', (aid, mentor,
                        'Parecer fictício: relaciona auth-03 e req-74 e reconhece evidências ausentes. A justificativa de contenção pode ser aprofundada na conversa.', now - 600))
                for stage, actor, timestamp in events:
                    connection.execute('INSERT INTO application_history(application_id,actor_id,status,created_at) VALUES(?,?,?,?)',
                        (aid, actor, stage, timestamp))
            connection.execute('CREATE TABLE demo_metadata(name TEXT PRIMARY KEY,value TEXT NOT NULL)')
            connection.execute('INSERT INTO demo_metadata VALUES(?,?)', ('fixture', DEMO_MARKER))
        if connection.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
            raise ValueError('Falha na integridade da demonstração.')
        if connection.execute('PRAGMA foreign_key_check').fetchall():
            raise ValueError('Falha nos vínculos da demonstração.')


def main():
    parser = argparse.ArgumentParser(description='Criar dados fictícios de apresentação em um banco NOVO, sem Docker.')
    parser.add_argument('destination', type=Path, help='Arquivo novo; lab.db e destinos existentes são recusados.')
    args = parser.parse_args()
    try:
        destination = prepare_demo(args.destination)
    except (OSError, ValueError, sqlite3.Error):
        parser.exit(1, 'Demonstração não criada. Use um destino novo diferente de lab.db e confira espaço/permissões. Nenhum destino existente é sobrescrito.\n')
    print(f'Demonstração criada: {destination}')
    print('Dados fictícios: duas vagas, uma candidatura com parecer/feedback e um rascunho retomável.')
    print('Acessos locais e roteiro: docs/APRESENTACAO.md. Nenhum e-mail é enviado.')


if __name__ == '__main__':
    main()
