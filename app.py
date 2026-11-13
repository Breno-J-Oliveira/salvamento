import base64, hashlib, os, secrets, sqlite3, threading, time, re
from datetime import timedelta
from pathlib import Path
from functools import wraps
from urllib.parse import urlsplit
from flask import Flask, g, render_template, request, redirect, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash
import orchestrator as orch
import learning
import recruitment
import selection
import rubric
import vacancies
import challenge_editor
import corporate
import remote_labs
from catalog import seed_catalog

app = Flask(__name__)
key_path = Path(__file__).parent / ".session-key"
if not os.environ.get("SECRET_KEY") and not key_path.exists():
    try:
        with key_path.open("x") as key_file:
            key_file.write(secrets.token_hex(32))
    except FileExistsError:
        pass
app.secret_key = os.environ.get("SECRET_KEY") or key_path.read_text().strip()
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                  MAX_CONTENT_LENGTH=65536, PERMANENT_SESSION_LIFETIME=timedelta(hours=8))
app.config['ALLOWED_HOSTS'] = ('127.0.0.1', 'localhost', '::1')
ENV_LOCK = threading.RLock()
RATE_LOCK = threading.Lock()
RATE_BUCKETS = {}


def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(32)
    return session["csrf"]

app.jinja_env.globals["csrf_token"] = csrf_token


@app.before_request
def protect_request():
    # SQLite identifiers are signed 64-bit integers; reject oversized route input.
    if any(isinstance(value,int) and value > 9223372036854775807
           for value in (request.view_args or {}).values()):
        abort(404)
    # Local deployment must not accept attacker-controlled DNS names.
    try:
        hostname = urlsplit(request.host_url).hostname
    except ValueError:
        abort(400)
    if hostname not in app.config['ALLOWED_HOSTS']:
        abort(400, description='Endereço de acesso não autorizado. Use o endereço local da aplicação.')
    # Machine credentials authenticate this single endpoint independently of browser cookies.
    if request.endpoint == 'remote_agent_poll':
        remote_labs.authenticate_agent(db)
        return
    if session.get("user_id"):
        user = db().execute("SELECT id,name,role FROM users WHERE id=?", (session["user_id"],)).fetchone()
        if not user:
            session.clear()
        else:
            session.update(name=user["name"], role=user["role"])
    if request.method == "POST":
        origin = request.headers.get('Origin')
        if origin and origin != request.host_url.rstrip('/'):
            abort(403, description='Origem da solicitação não autorizada.')
        if request.headers.get('Sec-Fetch-Site') == 'cross-site':
            abort(403, description='Origem da solicitação não autorizada.')
        if not secrets.compare_digest(session.get("csrf", "").encode("utf-8"), request.form.get("csrf_token", "").encode("utf-8")) or not session.get("csrf"):
            abort(400, description="A sessão do formulário expirou. Atualize a página e tente novamente.")
        auth_request = request.path in ("/login", "/register")
        # Authentication limits follow the client address even when a session exists.
        identity = str(request.remote_addr if auth_request else (session.get("user_id") or request.remote_addr))
        limit = 10 if auth_request else 40
        key = (identity, request.path)
        now = time.monotonic()
        with RATE_LOCK:
            for old_key in list(RATE_BUCKETS):
                if not RATE_BUCKETS[old_key] or now - RATE_BUCKETS[old_key][-1] >= 60:
                    del RATE_BUCKETS[old_key]
            recent = [t for t in RATE_BUCKETS.get(key, []) if now-t < 60]
            if len(recent) >= limit:
                abort(429, description="Muitas tentativas. Aguarde um minuto e tente novamente.")
            RATE_BUCKETS[key] = recent + [now]


@app.errorhandler(400)
@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(405)
@app.errorhandler(409)
@app.errorhandler(413)
@app.errorhandler(429)
def user_error(error):
    titles = {400: "Confira a solicitação", 403: "Acesso restrito", 404: "Página não encontrada", 405: "Ação não permitida", 409: "Confira a versão atual", 413: "Conteúdo muito grande", 429: "Aguarde um momento"}
    messages = {403: "Seu perfil não tem permissão para acessar esta área.", 404: "O item solicitado não existe ou não está disponível.", 405: "Use os botões disponíveis na página para realizar esta ação.", 413: "O formulário ultrapassou o limite de tamanho permitido."}
    return render_template("error.html", code=error.code, title=titles[error.code], message=messages.get(error.code, error.description)), error.code


@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    response.headers["Cache-Control"] = "no-store" if request.endpoint != "static" else "public, max-age=3600"
    return response


@app.errorhandler(sqlite3.OperationalError)
def persistence_error(error):
    busy = any(word in str(error).lower() for word in ('locked', 'busy'))
    code = 503 if busy else 500
    app.logger.error('Persistência indisponível: %s', type(error).__name__)
    response = app.make_response((render_template('error.html', code=code,
        title='Tente novamente em instantes' if busy else 'Não foi possível concluir',
        message='O sistema está ocupado. Aguarde alguns segundos e tente novamente.' if busy
        else 'A operação não foi concluída. Tente novamente; se persistir, avise a mentoria.'), code))
    if busy:
        response.headers['Retry-After'] = '5'
    return response
DB = os.environ.get("LAB_DATABASE") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "lab.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, password TEXT, role TEXT DEFAULT 'participante', team TEXT);
CREATE TABLE IF NOT EXISTS challenges(id INTEGER PRIMARY KEY, title TEXT, category TEXT, side TEXT, points INTEGER, description TEXT, hint TEXT, url TEXT, flag_hash TEXT);
CREATE TABLE IF NOT EXISTS attempts(id INTEGER PRIMARY KEY, user_id INTEGER, challenge_id INTEGER, correct INTEGER, created_at INTEGER);
CREATE TABLE IF NOT EXISTS instances(id INTEGER PRIMARY KEY, user_id INTEGER, challenge_id INTEGER, container TEXT, port INTEGER, flag_hash TEXT, started_at INTEGER, expires_at INTEGER, active INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS starts(user_id INTEGER, challenge_id INTEGER, started_at INTEGER, PRIMARY KEY(user_id, challenge_id));
CREATE TABLE IF NOT EXISTS jobs(id INTEGER PRIMARY KEY, title TEXT NOT NULL, company TEXT NOT NULL, description TEXT NOT NULL, side TEXT NOT NULL, min_points INTEGER NOT NULL, active INTEGER DEFAULT 1, created_by INTEGER, created_at INTEGER);
CREATE TABLE IF NOT EXISTS applications(id INTEGER PRIMARY KEY, job_id INTEGER NOT NULL, user_id INTEGER NOT NULL, created_at INTEGER, UNIQUE(job_id,user_id));
CREATE TABLE IF NOT EXISTS evaluations(id INTEGER PRIMARY KEY, user_id INTEGER, mentor_id INTEGER, logica INTEGER, comunicacao INTEGER, colaboracao INTEGER, decisao INTEGER, notes TEXT, created_at INTEGER);
"""

LOG = """10.0.0.5 - login falhou - usuario=maria
192.168.56.23 - login falhou - usuario=admin
192.168.56.23 - login falhou - usuario=root
10.0.0.8 - login ok - usuario=joao
192.168.56.23 - login falhou - usuario=admin
172.16.0.4 - login falhou - usuario=ana
192.168.56.23 - login falhou - usuario=teste"""

# (titulo, categoria, lado, pontos, descricao, dica, url, flag)
SEED = [
    ("Boas-vindas", "Geral", "Aquecimento", 50,
     "Sua primeira flag: CTF{bem_vindo_ao_purple_lab}. Copie e envie abaixo.", "Copie e cole.", "",
     "CTF{bem_vindo_ao_purple_lab}"),
    ("Intranet esquecida", "Web", "Red Team", 100,
     "Suba o container deste desafio (veja o README) e acesse a intranet. Existe um arquivo que os robôs de busca "
     "foram instruídos a ignorar. Encontre a flag.", "Todo site pode ter um /robots.txt.", "http://localhost:5001",
     "CTF{robots_txt_entrega_segredos}"),
    ("Texto estranho", "Criptografia", "Red Team", 100,
     "Interceptamos esta mensagem: " + base64.b64encode(b"CTF{base64_nao_e_criptografia}").decode()
     + "\nDecodifique-a para obter a flag.", "Isso é uma codificação, não uma cifra.", "",
     "CTF{base64_nao_e_criptografia}"),
    ("Quem está atacando?", "Análise de logs", "Blue Team", 150,
     "O servidor registrou os logs abaixo. Identifique o IP com mais falhas de login e envie a flag no formato "
     "CTF{ip}.\n\n" + LOG, "Conte as linhas 'login falhou' por IP.", "", "CTF{192.168.56.23}"),
]

def h(flag):
    return hashlib.sha256(flag.strip().encode()).hexdigest()

def init_db():
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA)
    con.executescript(learning.SCHEMA)
    recruitment.migrate(con)
    selection.migrate(con)
    rubric.migrate(con)
    vacancies.migrate(con)
    if not con.execute("SELECT 1 FROM users").fetchone():
        con.execute("INSERT INTO users(name,email,password,role,team) VALUES(?,?,?,?,?)",
                    ("Mentor", "mentor@cti.local", generate_password_hash(os.environ.get("MENTOR_PASSWORD", "mentor123")), "mentor", "Mentoria"))
    if not con.execute("SELECT 1 FROM challenges").fetchone():
        for t, c, s, p, d, hint, url, flag in SEED:
            con.execute("INSERT INTO challenges(title,category,side,points,description,hint,url,flag_hash) VALUES(?,?,?,?,?,?,?,?)",
                        (t, c, s, p, d, hint, url, h(flag)))
    cols = {r[1] for r in con.execute("PRAGMA table_info(challenges)")}
    for col, typ in (("image", "TEXT"), ("container_port", "INTEGER")):
        if col not in cols:
            con.execute(f"ALTER TABLE challenges ADD COLUMN {col} {typ}")
    con.execute("UPDATE challenges SET image='cti-lab/web-01', container_port=5000, url='', description=? "
                "WHERE title='Intranet esquecida' AND image IS NULL",
                ("Clique em 'Iniciar ambiente' para criar a sua intranet isolada e acesse o endereço mostrado. "
                 "Existe um arquivo que os robôs de busca foram instruídos a ignorar. Encontre a flag.",))
    seed_catalog(con)
    con.execute("INSERT INTO challenges(title,category,side,points,description,hint,url,flag_hash,image,container_port) "
                "SELECT ?,?,?,?,?,?,?,?,?,? WHERE NOT EXISTS (SELECT 1 FROM challenges WHERE title=?)",
                ("Incidente em andamento", "Resposta a incidentes", "Blue Team", 300,
                 "Investigue os registros disponíveis no servidor simulado. Identifique o endereço IP associado à atividade maliciosa e envie CTF{ip}.",
                 "", "", "", "cti-lab/incident-01", 5000, "Incidente em andamento"))
    challenge_editor.migrate(con)
    corporate.migrate(con)
    remote_labs.migrate(con)
    con.commit(); con.close()

def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB, timeout=30)
        g.db.execute("PRAGMA foreign_keys=ON")
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(_):
    d = g.pop("db", None)
    if d:
        d.close()

def login_required(f):
    @wraps(f)
    def w(*a, **k):
        if "user_id" not in session:
            return redirect("/login?next=" + request.path)
        return f(*a, **k)
    return w

def mentor_required(f):
    @wraps(f)
    @login_required
    def w(*a, **k):
        if session.get("role") != "mentor":
            abort(403)
        return f(*a, **k)
    return w

@app.route("/")
def index():
    d = db()
    own = next((r for r in stats() if r['id'] == session.get('user_id')), {})
    summary = dict(total=d.execute("SELECT COUNT(*) FROM challenges WHERE editorial_status='published'").fetchone()[0],
                   labs=d.execute("SELECT COUNT(*) FROM challenges WHERE image IS NOT NULL AND editorial_status='published'").fetchone()[0],
                   points=d.execute("SELECT COALESCE(SUM(points),0) FROM challenges WHERE editorial_status='published'").fetchone()[0],
                   own_points=own.get('points',0))
    # A mesma regra editorial da inscrição também protege os destaques públicos.
    now = int(time.time())
    featured_jobs = []
    for row in d.execute("SELECT * FROM jobs WHERE status='published' AND active=1 AND (deadline_at IS NULL OR deadline_at>?) ORDER BY created_at DESC,id DESC LIMIT 3", (now,)):
        if vacancies.is_open(row, now):
            featured_jobs.append(vacancies.decorate(row))
    return render_template('home.html', stats=summary, featured_jobs=featured_jobs)


@app.route('/labs')
@login_required
def laboratory():
    d=db(); now=int(time.time()); uid=session.get('user_id')
    items=[dict(r) for r in d.execute("SELECT * FROM challenges WHERE image IS NOT NULL AND editorial_status='published' ORDER BY CASE WHEN image='cti-lab/incident-01' THEN 0 ELSE 1 END,id")]
    instances={};solved=set();own_instances=[]
    if uid:
        own_instances=d.execute('SELECT * FROM instances WHERE user_id=? AND active=1 AND expires_at>=? ORDER BY started_at',(uid,now)).fetchall()
        instances={r['challenge_id']:dict(r) for r in own_instances}
        solved={r[0] for r in d.execute('SELECT DISTINCT challenge_id FROM attempts WHERE user_id=? AND correct=1',(uid,))}
    return render_template('laboratory.html',items=items,instances=instances,solved=solved,now=now,max_per_user=MAX_PER_USER,active_count=len(own_instances))


@app.route('/admin/laboratory-status', methods=['GET', 'POST'])
@mentor_required
def laboratory_status():
    diagnosis = orch.availability() if request.method == 'POST' else None
    return render_template('laboratory_status.html', diagnosis=diagnosis)


@app.route('/blog')
def study_blog():
    return render_template('blog.html')


@app.route('/purple-team')
def purple_team():
    return render_template('purple.html')

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        f = request.form
        name, email, password = f.get("name", "").strip(), f.get("email", "").strip().lower(), f.get("password", "")
        team = f.get("team", "").strip() or "Sem equipe"
        if not 2 <= len(name) <= 80 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) or len(email) > 254 or not 8 <= len(password) <= 128 or len(team) > 80:
            flash("Confira os campos: nome de 2 a 80 caracteres, e-mail válido, senha de 8 a 128 caracteres e equipe com até 80 caracteres.")
            return render_template("register.html"), 400
        try:
            db().execute("INSERT INTO users(name,email,password,team) VALUES(?,?,?,?)",
                         (name, email, generate_password_hash(password), team))
            db().commit()
            flash("Conta criada! Faça login.")
            target = recruitment.safe_next(request.form.get("next") or request.args.get("next"))
            return redirect("/login?next=" + target if target else "/login")
        except sqlite3.IntegrityError:
            flash("Este e-mail já está cadastrado.")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = db().execute("SELECT * FROM users WHERE email=?", (request.form.get("email", "").strip().lower(),)).fetchone()
        if len(request.form.get("password", "")) <= 128 and u and check_password_hash(u["password"], request.form.get("password", "")):
            session.clear()
            session.update(user_id=u["id"], name=u["name"], role=u["role"])
            session.permanent = True
            if u["role"] == "mentor":
                return redirect("/admin")
            return redirect(recruitment.safe_next(request.form.get("next") or request.args.get("next")) or "/my-applications")
        flash("E-mail ou senha inválidos.")
    return render_template("login.html")

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect("/login")

@app.route("/challenges")
@login_required
def challenges():
    d = db()
    solved = {r[0] for r in d.execute("SELECT challenge_id FROM attempts WHERE user_id=? AND correct=1", (session["user_id"],))}
    return render_template("challenges.html", items=d.execute("SELECT * FROM challenges WHERE editorial_status='published' ORDER BY id").fetchall(), solved=solved)

TTL = 60 * 60       # duração de cada ambiente: 60 minutos
MAX_ACTIVE = 10     # máximo de containers ao mesmo tempo
MAX_PER_USER = 2    # máximo por participante

def reap_expired():
    with ENV_LOCK:
        con = sqlite3.connect(DB, timeout=30)
        try:
            now = int(time.time())
            for iid, name in con.execute("SELECT id,container FROM instances WHERE active=1 AND expires_at<?", (now,)).fetchall():
                try:
                    orch.stop(name)
                except orch.DockerError:
                    app.logger.warning("Não foi possível encerrar ambiente expirado %s", iid)
                    continue
                con.execute("UPDATE instances SET active=0 WHERE id=?", (iid,))
                con.commit()
        finally:
            con.close()


def reaper_loop():
    while True:
        time.sleep(60)
        try:
            reap_expired()
        except sqlite3.Error:
            app.logger.warning("Não foi possível consultar ambientes expirados")


def active_instance(d, uid, cid):
    return d.execute("SELECT * FROM instances WHERE user_id=? AND challenge_id=? AND active=1 AND expires_at>=?",
                     (uid, cid, int(time.time()))).fetchone()

def stop_instance(d, row):
    try:
        orch.stop(row["container"])
    except orch.DockerError:
        flash("Não foi possível encerrar o ambiente. Verifique o Docker e tente novamente.")
        return False
    d.execute("UPDATE instances SET active=0 WHERE id=?", (row["id"],))
    d.commit()
    return True

@app.route("/challenge/<int:cid>", methods=["GET", "POST"])
@login_required
def challenge(cid):
    d, uid = db(), session["user_id"]
    c = d.execute("SELECT * FROM challenges WHERE id=?", (cid,)).fetchone()
    if not c or (c["editorial_status"] != "published" and (session.get("role") != "mentor" or request.method == "POST")):
        abort(404)
    d.execute("INSERT OR IGNORE INTO starts VALUES(?,?,?)", (uid, cid, int(time.time())))
    d.commit()
    solved = d.execute("SELECT 1 FROM attempts WHERE user_id=? AND challenge_id=? AND correct=1", (uid, cid)).fetchone() is not None
    if request.method == "POST" and solved:
        return redirect(f"/challenge/{cid}")
    if request.method == "POST" and not solved:
        d.execute("BEGIN IMMEDIATE")
        c = d.execute("SELECT * FROM challenges WHERE id=?", (cid,)).fetchone()
        if not c or c["editorial_status"] != "published":
            d.rollback()
            abort(404)
        if d.execute("SELECT 1 FROM attempts WHERE user_id=? AND challenge_id=? AND correct=1", (uid,cid)).fetchone():
            d.rollback()
            return redirect(f"/challenge/{cid}")
        flag = request.form.get("flag", "")
        if not flag.strip() or len(flag) > 512:
            d.rollback()
            flash("Informe uma flag com até 512 caracteres.")
            return redirect(f"/challenge/{cid}")
        if c["image"]:   # desafio com ambiente: resposta vinculada à instância
            if c['image'] == 'cti-lab/incident-01':
                failures = d.execute('SELECT COUNT(*) FROM attempts WHERE user_id=? AND challenge_id=? AND correct=0 AND created_at>=?',
                                     (uid, cid, int(time.time()) - 86400)).fetchone()[0]
                if failures >= 12:
                    d.rollback()
                    abort(429, description='Limite de 12 respostas incorretas em 24 horas atingido neste cenário. Aguarde a renovação do período.')
            hashes = [r[0] for r in d.execute("SELECT flag_hash FROM instances WHERE user_id=? AND challenge_id=? AND active=1 AND expires_at>=?", (uid, cid, int(time.time())))]
            if not hashes:
                d.rollback()
                flash("Inicie o seu ambiente antes de enviar a flag.")
                return redirect(f"/challenge/{cid}")
            ok = h(flag) in hashes
        else:
            ok = h(flag) == c["flag_hash"]
        d.execute("INSERT INTO attempts(user_id,challenge_id,correct,created_at) VALUES(?,?,?,?)", (uid, cid, int(ok), int(time.time())))
        d.commit()
        flash("Flag correta!" if ok else "Flag incorreta. Tente de novo.")
        return redirect(f"/challenge/{cid}")
    inst = active_instance(d, uid, cid) if c["image"] else None
    if inst:
        inst = dict(inst)
        try:
            inst["available"] = orch.status(inst["container"])
            if not inst["available"]:
                d.execute("UPDATE instances SET active=0 WHERE id=?", (inst["id"],))
                d.commit()
                inst = None
                flash("O ambiente não está mais em execução. Você pode iniciar outro.")
        except orch.DockerError:
            inst["available"] = False
    return render_template("challenge.html", c=c, solved=solved, inst=inst, now=int(time.time()))

@app.route("/challenge/<int:cid>/start", methods=["POST"])
@login_required
def start_env(cid):
    with ENV_LOCK:
        return start_env_locked(cid)


def start_env_locked(cid):
    d, uid = db(), session["user_id"]
    c = d.execute("SELECT * FROM challenges WHERE id=?", (cid,)).fetchone()
    if not c or not c["image"] or c["editorial_status"] != "published":
        abort(404)
    reap_expired()
    back = redirect(f"/challenge/{cid}")
    existing = active_instance(d, uid, cid)
    if existing:
        try:
            running = orch.status(existing["container"])
        except orch.DockerError:
            flash("Não foi possível consultar o ambiente. Verifique o Docker e tente novamente.")
            return back
        if running:
            return back
        d.execute("UPDATE instances SET active=0 WHERE id=?", (existing["id"],))
        d.commit()
    if d.execute("SELECT COUNT(*) FROM instances WHERE active=1").fetchone()[0] >= MAX_ACTIVE:
        flash("O laboratório está cheio no momento. Tente novamente em alguns minutos.")
        return back
    if d.execute("SELECT COUNT(*) FROM instances WHERE user_id=? AND active=1", (uid,)).fetchone()[0] >= MAX_PER_USER:
        flash(f"Você já tem {MAX_PER_USER} ambientes ativos. Encerre um antes de iniciar outro.")
        return back
    flag = "CTF{" + secrets.token_hex(8) + "}"
    name = f"lab-u{uid}-c{cid}-{secrets.token_hex(3)}"
    try:
        port = orch.start(name, c["image"], c["container_port"], flag)
    except orch.DockerError:
        flash("Não foi possível iniciar o ambiente. Verifique se o Docker Desktop está em execução e tente novamente.")
        return back
    now = int(time.time())
    try:
        answer = f"CTF{{192.0.2.{1 + int(flag[4:6], 16) % 254}}}" if c["image"] == "cti-lab/incident-01" else flag
        d.execute("INSERT INTO instances(user_id,challenge_id,container,port,flag_hash,started_at,expires_at,active) VALUES(?,?,?,?,?,?,?,1)",
                  (uid, cid, name, port, h(answer), now, now + TTL))
        d.commit()
    except sqlite3.Error:
        d.rollback()
        orch.stop(name)
        raise
    flash(f"Ambiente iniciado! Ele expira em {TTL // 60} minutos.")
    return back

@app.route("/challenge/<int:cid>/stop", methods=["POST"])
@login_required
def stop_env(cid):
    d = db()
    row = d.execute("SELECT * FROM instances WHERE user_id=? AND challenge_id=? AND active=1", (session["user_id"], cid)).fetchone()
    if row:
        if stop_instance(d, row):
            flash("Ambiente encerrado.")
    return redirect(f"/challenge/{cid}")

@app.route("/ambientes")
@mentor_required
def ambientes():
    reap_expired()
    rows = db().execute("""SELECT i.*, u.name uname, c.title FROM instances i
                           JOIN users u ON u.id=i.user_id JOIN challenges c ON c.id=i.challenge_id
                           WHERE i.active=1 ORDER BY i.id""").fetchall()
    return render_template("ambientes.html", rows=rows, now=int(time.time()), max=MAX_ACTIVE)

@app.route("/ambientes/<int:iid>/encerrar", methods=["POST"])
@mentor_required
def encerrar_ambiente(iid):
    d = db()
    row = d.execute("SELECT * FROM instances WHERE id=? AND active=1", (iid,)).fetchone()
    if row:
        stop_instance(d, row)
    return redirect("/ambientes")

@app.route("/ambientes/encerrar-todos", methods=["POST"])
@mentor_required
def encerrar_todos():
    d = db()
    results = [stop_instance(d, row) for row in d.execute("SELECT * FROM instances WHERE active=1").fetchall()]
    if all(results):
        flash("Todos os ambientes foram encerrados.")
    return redirect("/ambientes")

def stats():
    # Agrega cada conjunto uma vez; evita consultas por participante no ranking.
    rows = db().execute("""
        WITH solved AS (
            SELECT a.user_id,a.challenge_id,MIN(a.created_at) finished
            FROM attempts a WHERE a.correct=1 GROUP BY a.user_id,a.challenge_id
        ), scores AS (
            SELECT s.user_id,COUNT(*) solved,SUM(c.points) points,
                AVG(CASE WHEN st.started_at IS NOT NULL THEN MAX(0,s.finished-st.started_at)/60.0 END) avg_min
            FROM solved s JOIN challenges c ON c.id=s.challenge_id
            LEFT JOIN starts st ON st.user_id=s.user_id AND st.challenge_id=s.challenge_id
            GROUP BY s.user_id
        ), tries AS (SELECT user_id,COUNT(*) attempts FROM attempts GROUP BY user_id),
        ratings AS (SELECT user_id,AVG((logica+comunicacao+colaboracao+decisao)/4.0) rating FROM evaluations GROUP BY user_id)
        SELECT u.id,u.name,u.team,COALESCE(s.solved,0) solved,COALESCE(s.points,0) points,
            COALESCE(t.attempts,0) attempts,ROUND(s.avg_min,1) avg_min,ROUND(r.rating,1) rating
        FROM users u LEFT JOIN scores s ON s.user_id=u.id LEFT JOIN tries t ON t.user_id=u.id
        LEFT JOIN ratings r ON r.user_id=u.id WHERE u.role='participante'
        ORDER BY points DESC,u.id
    """).fetchall()
    return [dict(row) for row in rows]

@app.route("/dashboard")
@mentor_required
def dashboard():
    rows = stats()
    teams = {}
    for r in rows:
        t = teams.setdefault(r["team"], dict(team=r["team"], members=0, solved=0, points=0, attempts=0))
        t["members"] += 1
        for k in ("solved", "points", "attempts"):
            t[k] += r[k]
    total = db().execute("SELECT COUNT(*) FROM challenges").fetchone()[0]
    return render_template("dashboard.html", rows=rows, teams=sorted(teams.values(), key=lambda t: -t["points"]), total=total)

@app.route("/participante/<int:uid>", methods=["GET", "POST"])
@mentor_required
def participante(uid):
    d = db()
    u = d.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    if not u or u["role"] != "participante":
        abort(404)
    if request.method == "POST":
        try:
            v = [int(request.form.get(k, "")) for k in ("logica", "comunicacao", "colaboracao", "decisao")]
        except ValueError:
            abort(400, description="As notas devem ser números inteiros entre 1 e 5.")
        if any(n < 1 or n > 5 for n in v) or len(request.form.get("notes", "")) > 4000:
            abort(400, description="Confira as notas e limite as observações a 4000 caracteres.")
        d.execute("INSERT INTO evaluations(user_id,mentor_id,logica,comunicacao,colaboracao,decisao,notes,created_at) VALUES(?,?,?,?,?,?,?,?)",
                  (uid, session["user_id"], *v, request.form.get("notes", ""), int(time.time())))
        d.commit()
        flash("Avaliação registrada.")
        return redirect(f"/participante/{uid}")
    attempts = d.execute("""SELECT c.title, a.correct, a.created_at FROM attempts a JOIN challenges c ON c.id=a.challenge_id
                            WHERE a.user_id=? ORDER BY a.id DESC""", (uid,)).fetchall()
    evals = d.execute("SELECT * FROM evaluations WHERE user_id=? ORDER BY id DESC", (uid,)).fetchall()
    return render_template("participante.html", u=u, attempts=attempts, evals=evals, writeups=d.execute("SELECT c.title,w.content FROM writeups w JOIN challenges c ON c.id=w.challenge_id WHERE w.user_id=? ORDER BY w.updated_at DESC",(uid,)).fetchall(),
                           s=next((r for r in stats() if r["id"] == uid), None), fmt=lambda t: time.strftime("%d/%m %H:%M", time.localtime(t)))

@app.route("/ranking")
@login_required
def ranking():
    return render_template("ranking.html", rows=stats(), total=db().execute("SELECT COUNT(*) FROM challenges").fetchone()[0])


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        name, team = request.form.get("name", "").strip(), request.form.get("team", "").strip() or "Sem equipe"
        if not 2 <= len(name) <= 80 or len(team) > 80:
            abort(400, description="Nome deve ter de 2 a 80 caracteres; equipe até 80.")
        db().execute("UPDATE users SET name=?,team=? WHERE id=?", (name, team, session["user_id"]))
        db().commit()
        session["name"] = name
        flash("Perfil atualizado.")
        return redirect("/profile")
    user = db().execute("SELECT id,name,email,team,role FROM users WHERE id=?", (session["user_id"],)).fetchone()
    return render_template("profile.html", user=user, s=next((r for r in stats() if r["id"] == user["id"]), None))


@app.route("/jobs", methods=["GET", "POST"])
@login_required
def jobs():
    if request.method == "POST":
        if session.get("role") != "mentor":
            abort(403)
        f = request.form
        title, company, description, side = [f.get(k, "").strip() for k in ("title", "company", "description", "side")]
        try:
            points = int(f.get("min_points", ""))
        except ValueError:
            abort(400, description="A pontuação mínima deve ser um número inteiro.")
        if not 3 <= len(title) <= 120 or not 2 <= len(company) <= 120 or not 10 <= len(description) <= 4000 or side not in ("Red Team", "Blue Team", "Purple Team") or not 0 <= points <= 100000:
            abort(400, description="Confira os dados da vaga e a pontuação mínima.")
        created = db().execute("INSERT INTO jobs(title,company,description,side,min_points,created_by,created_at) VALUES(?,?,?,?,?,?,?)", (title,company,description,side,points,session["user_id"],int(time.time())))
        vacancies.event(db(),created.lastrowid,session["user_id"],"created",None,"published",1)
        db().commit()
        flash("Vaga publicada.")
        return redirect("/jobs")
    rows = [vacancies.decorate(r) for r in db().execute("SELECT * FROM jobs ORDER BY id DESC")]
    if session.get("role") != "mentor":
        rows = [row for row in rows if vacancies.is_open(row)]
    own = next((r for r in stats() if r["id"] == session["user_id"]), {"points": 0})
    applied = {r[0] for r in db().execute("SELECT job_id FROM applications WHERE user_id=?", (session["user_id"],))}
    applicants = {}
    if session['role'] == 'mentor':
        for candidate in db().execute('''SELECT a.job_id,u.id,u.name,a.created_at
                FROM applications a JOIN users u ON u.id=a.user_id WHERE a.status!='draft' ORDER BY a.id'''):
            applicants.setdefault(candidate['job_id'], []).append(candidate)
    for row in rows:
        row["match_score"] = min(100, round(own["points"] / row["min_points"] * 100)) if row["min_points"] else 100
        row["applied"] = row["id"] in applied
        row["applicants"] = applicants.get(row['id'], [])
    return render_template("jobs.html", jobs=rows)


@app.route("/jobs/<int:jid>/apply", methods=["POST"])
@login_required
def apply_job(jid):
    if session["role"] != "participante":
        abort(403)
    job = db().execute("SELECT * FROM jobs WHERE id=?", (jid,)).fetchone()
    if not job or not vacancies.is_open(job):
        abort(404)
    return redirect(f"/applications/{jid}/form")


@app.route("/jobs/<int:jid>/toggle", methods=["POST"])
@mentor_required
def toggle_job(jid):
    target = request.form.get('active')
    if target is not None and target not in ('0','1'):
        abort(400,description='Informe um estado válido para a oportunidade.')
    d=db();d.execute('BEGIN IMMEDIATE')
    row=d.execute('SELECT * FROM jobs WHERE id=?',(jid,)).fetchone()
    if not row:abort(404)
    old=vacancies.state(row)
    if old not in ('published','paused'):
        abort(400,description='Use o editor para publicar rascunhos. Vagas encerradas não podem ser reabertas.')
    new='published' if (target=='1' or (target is None and old=='paused')) else 'paused'
    if new=='published' and row['deadline_at'] is not None and row['deadline_at']<=int(time.time()):
        abort(400,description='Atualize o prazo pelo editor antes de reabrir a vaga.')
    if new!=old:
        d.execute('UPDATE jobs SET active=?,status=?,revision=revision+1,updated_at=? WHERE id=?',(int(new=='published'),new,int(time.time()),jid))
        vacancies.event(d,jid,session['user_id'],'state_changed',old,new,row['revision']+1)
    d.commit()
    return redirect('/jobs')


challenge_editor.register_routes(app, db, mentor_required)
corporate.register_routes(app, db, login_required, mentor_required)
remote_labs.register_routes(app, db, login_required, mentor_required)
learning.register_routes(app, db, login_required)
recruitment.register_routes(app, db, login_required, mentor_required)
selection.register_routes(app, db, login_required)
rubric.register_routes(app, db, mentor_required)
vacancies.register_routes(app, db, mentor_required)

if __name__ == "__main__":
    init_db()
    threading.Thread(target=reaper_loop, daemon=True).start()
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False, use_reloader=False)
