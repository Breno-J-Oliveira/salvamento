"""Single-use remote Linux workers and a private, observable command journal.

The worker executes commands inside a separately provisioned VM. This module
never executes participant commands on the Flask host and never provisions VMs.
"""
import hashlib
import secrets
import time
import uuid

from flask import abort, jsonify, redirect, render_template, request, session

STATES = {
    'active': 'Em andamento', 'ended': 'Encerrada', 'expired': 'Tempo esgotado',
    'queued': 'Na fila', 'running': 'Executando', 'completed': 'Concluído',
    'failed': 'Falhou', 'interrupted': 'Interrompido',
    'available': 'Disponível', 'allocated': 'Em uso', 'retired': 'Aguardando recriação',
}
HEARTBEAT_SECONDS = 30
COMMAND_TIMEOUT = 25
SESSION_SECONDS = 1800


def migrate(con):
    con.executescript('''
    CREATE TABLE IF NOT EXISTS remote_machines(
        id INTEGER PRIMARY KEY, name TEXT NOT NULL,
        token_hash TEXT NOT NULL UNIQUE,
        status TEXT NOT NULL DEFAULT 'available'
            CHECK(status IN ('available','allocated','retired')),
        last_seen INTEGER);
    CREATE TABLE IF NOT EXISTS remote_sessions(
        id INTEGER PRIMARY KEY,
        machine_id INTEGER NOT NULL REFERENCES remote_machines(id),
        user_id INTEGER NOT NULL REFERENCES users(id),
        status TEXT NOT NULL DEFAULT 'active'
            CHECK(status IN ('active','ended','expired')),
        started_at INTEGER NOT NULL, expires_at INTEGER NOT NULL,
        ended_at INTEGER, consent_at INTEGER NOT NULL);
    CREATE UNIQUE INDEX IF NOT EXISTS idx_remote_active_user
        ON remote_sessions(user_id) WHERE status='active';
    CREATE UNIQUE INDEX IF NOT EXISTS idx_remote_active_machine
        ON remote_sessions(machine_id) WHERE status='active';
    CREATE TABLE IF NOT EXISTS remote_commands(
        id INTEGER PRIMARY KEY,
        session_id INTEGER NOT NULL REFERENCES remote_sessions(id),
        command TEXT NOT NULL, request_key TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'queued'
            CHECK(status IN ('queued','running','completed','failed','interrupted')),
        lease_token TEXT, queued_at INTEGER NOT NULL,
        started_at INTEGER, finished_at INTEGER,
        output TEXT NOT NULL DEFAULT '', exit_code INTEGER,
        UNIQUE(session_id,request_key));
    CREATE UNIQUE INDEX IF NOT EXISTS idx_remote_pending_command
        ON remote_commands(session_id) WHERE status IN ('queued','running');
    CREATE TABLE IF NOT EXISTS remote_notes(
        id INTEGER PRIMARY KEY,
        session_id INTEGER NOT NULL REFERENCES remote_sessions(id),
        mentor_id INTEGER NOT NULL REFERENCES users(id),
        body TEXT NOT NULL, created_at INTEGER NOT NULL);
    CREATE INDEX IF NOT EXISTS idx_remote_commands_session
        ON remote_commands(session_id,id);
    CREATE INDEX IF NOT EXISTS idx_remote_notes_session
        ON remote_notes(session_id,id);
    ''')


def authenticate_agent(db):
    """Dedicated bearer authentication, independent of browser sessions/CSRF."""
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        abort(401)
    token = auth[7:]
    if not 32 <= len(token) <= 256 or not token.isascii():
        abort(401)
    digest = hashlib.sha256(token.encode('ascii')).hexdigest()
    machine = db().execute('SELECT * FROM remote_machines WHERE token_hash=?', (digest,)).fetchone()
    if not machine or not secrets.compare_digest(machine['token_hash'], digest):
        abort(401)
    return machine


def valid_text(value, maximum):
    if not isinstance(value, str) or len(value) > maximum or '\x00' in value:
        return False
    try:
        value.encode('utf-8')
    except UnicodeEncodeError:
        return False
    return True


def finish_session(con, item, now, status):
    con.execute('UPDATE remote_sessions SET status=?,ended_at=? WHERE id=? AND status=\'active\'',
                (status, now, item['id']))
    con.execute("UPDATE remote_machines SET status='retired' WHERE id=?", (item['machine_id'],))
    con.execute("UPDATE remote_commands SET status='interrupted',finished_at=? "
                "WHERE session_id=? AND status IN ('queued','running')", (now, item['id']))


def maintenance(con, now):
    for item in con.execute("SELECT id,machine_id FROM remote_sessions WHERE status='active' AND expires_at<=?", (now,)).fetchall():
        finish_session(con, item, now, 'expired')
    # A lost acknowledgement never causes a command to execute twice.
    con.execute("UPDATE remote_commands SET status='interrupted',finished_at=? "
                "WHERE status='running' AND started_at<=?", (now, now - 45))


def register_routes(app, db, login_required, mentor_required):
    def transaction():
        con = db()
        con.execute('BEGIN IMMEDIATE')
        maintenance(con, int(time.time()))
        return con

    def get_session(sid):
        row = db().execute('SELECT s.*,u.name user_name,m.name machine_name,m.last_seen '
                           'FROM remote_sessions s JOIN users u ON u.id=s.user_id '
                           'JOIN remote_machines m ON m.id=s.machine_id WHERE s.id=?', (sid,)).fetchone()
        if not row:
            abort(404)
        if session.get('role') != 'mentor' and row['user_id'] != session.get('user_id'):
            abort(403)
        return dict(row)

    def participant():
        if session.get('role') != 'participante':
            abort(403)

    def journal(sid):
        return [dict(row) for row in db().execute(
            'SELECT id,command,status,output,exit_code,queued_at,started_at,finished_at '
            'FROM remote_commands WHERE session_id=? ORDER BY id', (sid,))]

    def private_notes(sid):
        if session.get('role') != 'mentor':
            return []
        return [dict(row) for row in db().execute(
            'SELECT n.id,n.body,n.created_at,u.name mentor_name FROM remote_notes n '
            'JOIN users u ON u.id=n.mentor_id WHERE n.session_id=? ORDER BY n.id', (sid,))]

    @app.get('/remote-labs')
    @login_required
    def remote_labs():
        con = transaction()
        con.commit()
        now = int(time.time())
        machines = [dict(row) for row in con.execute('SELECT id,name,status,last_seen FROM remote_machines ORDER BY id')]
        for machine in machines:
            machine['online'] = bool(machine['last_seen'] and machine['last_seen'] > now - HEARTBEAT_SECONDS)
        where = '' if session.get('role') == 'mentor' else 'WHERE s.user_id=?'
        params = () if session.get('role') == 'mentor' else (session['user_id'],)
        rows = con.execute('SELECT s.*,u.name user_name,m.name machine_name FROM remote_sessions s '
                           'JOIN users u ON u.id=s.user_id JOIN remote_machines m ON m.id=s.machine_id '
                           + where + ' ORDER BY s.id DESC LIMIT 100', params).fetchall()
        return render_template('remote_labs.html', machines=machines,
                               sessions=[dict(row) for row in rows], states=STATES)

    @app.post('/remote-labs/start')
    @login_required
    def remote_start():
        participant()
        if request.form.get('consent') != 'yes':
            abort(400, description='Confirme que compreende o acompanhamento e o registro do terminal.')
        con = transaction()
        existing = con.execute("SELECT id FROM remote_sessions WHERE user_id=? AND status='active'", (session['user_id'],)).fetchone()
        if existing:
            con.commit()
            return redirect(f'/remote-labs/{existing["id"]}')
        now = int(time.time())
        machine = con.execute("SELECT id FROM remote_machines WHERE status='available' AND last_seen>? ORDER BY id LIMIT 1",
                              (now - HEARTBEAT_SECONDS,)).fetchone()
        if not machine:
            con.commit()
            abort(409, description='Nenhuma máquina está disponível. Aguarde a preparação pela equipe.')
        cursor = con.execute('INSERT INTO remote_sessions(machine_id,user_id,started_at,expires_at,consent_at) VALUES(?,?,?,?,?)',
                             (machine['id'], session['user_id'], now, now + SESSION_SECONDS, now))
        con.execute("UPDATE remote_machines SET status='allocated' WHERE id=?", (machine['id'],))
        con.commit()
        return redirect(f'/remote-labs/{cursor.lastrowid}')

    @app.get('/remote-labs/<int:sid>')
    @login_required
    def remote_session(sid):
        con = transaction()
        item = get_session(sid)
        con.commit()
        item['machine_online'] = bool(item['last_seen'] and item['last_seen'] > int(time.time()) - HEARTBEAT_SECONDS)
        return render_template('remote_session.html', item=item, commands=journal(sid),
                               notes=private_notes(sid), observer=session.get('role') == 'mentor',
                               states=STATES, request_key=str(uuid.uuid4()))

    @app.get('/remote-labs/<int:sid>/events')
    @login_required
    def remote_events(sid):
        con = transaction()
        item = get_session(sid)
        con.commit()
        return jsonify(session=dict(id=item['id'], status=item['status'], expires_at=item['expires_at'],
                                    machine_online=bool(item['last_seen'] and item['last_seen'] > int(time.time()) - HEARTBEAT_SECONDS)),
                       commands=journal(sid), notes=private_notes(sid))

    @app.post('/remote-labs/<int:sid>/commands')
    @login_required
    def remote_command(sid):
        participant()
        command = request.form.get('command', '').strip()
        key = request.form.get('request_key', '')
        try:
            if str(uuid.UUID(key)) != key:
                raise ValueError()
        except (ValueError, AttributeError):
            abort(400, description='Atualize a página antes de enviar o comando.')
        if not command or not valid_text(command, 1000):
            abort(400, description='Informe um comando com até 1.000 caracteres.')
        con = transaction()
        item = get_session(sid)
        previous = con.execute('SELECT command FROM remote_commands WHERE session_id=? AND request_key=?', (sid, key)).fetchone()
        if previous:
            if previous['command'] != command:
                abort(409, description='Este envio já contém outro comando. Atualize a página.')
            con.commit()
            return redirect(f'/remote-labs/{sid}')
        if item['status'] != 'active':
            con.commit()
            abort(409, description='A sessão foi encerrada.')
        if not item['last_seen'] or item['last_seen'] <= int(time.time()) - HEARTBEAT_SECONDS:
            con.commit()
            abort(409, description='A máquina perdeu a conexão. Aguarde o retorno do agente.')
        if con.execute("SELECT 1 FROM remote_commands WHERE session_id=? AND status IN ('queued','running')", (sid,)).fetchone():
            abort(409, description='Aguarde o comando anterior terminar.')
        if con.execute('SELECT COUNT(*) FROM remote_commands WHERE session_id=?', (sid,)).fetchone()[0] >= 200:
            abort(409, description='Esta sessão atingiu o limite de 200 comandos.')
        con.execute('INSERT INTO remote_commands(session_id,command,request_key,queued_at) VALUES(?,?,?,?)',
                    (sid, command, key, int(time.time())))
        con.commit()
        return redirect(f'/remote-labs/{sid}')

    @app.post('/remote-labs/<int:sid>/end')
    @login_required
    def remote_end(sid):
        con = transaction()
        item = get_session(sid)
        if item['status'] == 'active':
            finish_session(con, item, int(time.time()), 'ended')
        con.commit()
        return redirect(f'/remote-labs/{sid}')

    @app.post('/remote-labs/<int:sid>/notes')
    @mentor_required
    def remote_note(sid):
        body = request.form.get('body', '').strip()
        if not body or not valid_text(body, 4000):
            abort(400, description='Escreva uma anotação com até 4.000 caracteres.')
        con = transaction()
        get_session(sid)
        if con.execute('SELECT COUNT(*) FROM remote_notes WHERE session_id=?', (sid,)).fetchone()[0] >= 200:
            abort(409, description='Esta sessão atingiu o limite de anotações.')
        con.execute('INSERT INTO remote_notes(session_id,mentor_id,body,created_at) VALUES(?,?,?,?)',
                    (sid, session['user_id'], body, int(time.time())))
        con.commit()
        return redirect(f'/remote-labs/{sid}')

    @app.post('/api/lab-agent/poll')
    def remote_agent_poll():
        machine = authenticate_agent(db)
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or set(payload) - {'result'}:
            abort(400)
        result = payload.get('result')
        if result is not None:
            if (not isinstance(result, dict) or set(result) != {'command_id', 'lease_token', 'output', 'exit_code'}
                    or type(result['command_id']) is not int or not 0 < result['command_id'] < 2**63
                    or not valid_text(result['lease_token'], 128)
                    or not valid_text(result['output'], 16000)
                    or type(result['exit_code']) is not int or not -65536 <= result['exit_code'] <= 65536):
                abort(400)
        con = transaction()
        now = int(time.time())
        con.execute('UPDATE remote_machines SET last_seen=? WHERE id=?', (now, machine['id']))
        if result is not None:
            row = con.execute('SELECT c.* FROM remote_commands c JOIN remote_sessions s ON s.id=c.session_id '
                              'WHERE c.id=? AND s.machine_id=?', (result['command_id'], machine['id'])).fetchone()
            if not row or not row['lease_token'] or not secrets.compare_digest(
                    row['lease_token'].encode('utf-8'), result['lease_token'].encode('utf-8')):
                abort(409)
            if row['status'] == 'running':
                con.execute('UPDATE remote_commands SET status=?,output=?,exit_code=?,finished_at=? WHERE id=?',
                            ('completed' if result['exit_code'] == 0 else 'failed', result['output'],
                             result['exit_code'], now, row['id']))
            # Completed results and late acknowledgements are accepted without
            # rewriting history or restarting the command.
        item = con.execute("SELECT * FROM remote_sessions WHERE machine_id=? AND status='active'", (machine['id'],)).fetchone()
        current = con.execute('SELECT status FROM remote_machines WHERE id=?', (machine['id'],)).fetchone()
        state = 'active' if item else ('retired' if current['status'] == 'retired' else 'idle')
        job = None
        if item:
            row = con.execute("SELECT id,command FROM remote_commands WHERE session_id=? AND status='queued' ORDER BY id LIMIT 1", (item['id'],)).fetchone()
            if row:
                lease = secrets.token_urlsafe(32)
                con.execute("UPDATE remote_commands SET status='running',lease_token=?,started_at=? WHERE id=?", (lease, now, row['id']))
                job = dict(command_id=row['id'], lease_token=lease, command=row['command'], timeout=COMMAND_TIMEOUT)
        con.commit()
        return jsonify(state=state, session_id=item['id'] if item else None,
                       expires_at=item['expires_at'] if item else None, job=job)
