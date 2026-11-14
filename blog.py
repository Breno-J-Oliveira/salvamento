"""Artigos do blog de estudos mantidos pela equipe (mentoria)."""
import time

SCHEMA = """
CREATE TABLE IF NOT EXISTS blog_posts(
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  category TEXT NOT NULL,
  summary TEXT NOT NULL DEFAULT '',
  body TEXT NOT NULL,
  link_url TEXT NOT NULL DEFAULT '',
  link_label TEXT NOT NULL DEFAULT '',
  published INTEGER NOT NULL DEFAULT 1,
  author_id INTEGER REFERENCES users(id),
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);
"""

CATEGORIES = ('Web', 'Cripto', 'Blue Team', 'Red Team', 'Logs', 'Forense', 'Hardening', 'Resposta a incidentes', 'VirtualBox', 'Carreira')


def migrate(con):
    con.executescript(SCHEMA)


def clean(form):
    """Valida o formulário e devolve (dados, erros)."""
    data = {k: (form.get(k) or '').strip() for k in ('title', 'category', 'summary', 'body', 'link_url', 'link_label')}
    data['published'] = 1 if form.get('published') else 0
    errors = []
    if not 3 <= len(data['title']) <= 120:
        errors.append('O título deve ter de 3 a 120 caracteres.')
    if data['category'] not in CATEGORIES:
        errors.append('Escolha uma categoria da lista.')
    if len(data['summary']) > 280:
        errors.append('O resumo pode ter até 280 caracteres.')
    if not 20 <= len(data['body']) <= 8000:
        errors.append('O texto do artigo deve ter de 20 a 8000 caracteres.')
    link = data['link_url']
    # Apenas páginas da própria plataforma ou endereços https.
    if link and not ((link.startswith('/') and not link.startswith('//')) or link.startswith('https://')):
        errors.append('O link deve ser uma página da plataforma (ex.: /challenges) ou um endereço https://.')
    if len(link) > 300 or len(data['link_label']) > 80:
        errors.append('Link ou texto do link muito longo.')
    if link and not data['link_label']:
        data['link_label'] = 'Saiba mais'
    return data, errors


def paragraphs(body):
    return [p.strip() for p in body.replace('\r\n', '\n').split('\n\n') if p.strip()]


def save(con, data, author_id, post_id=None):
    now = int(time.time())
    if post_id:
        con.execute('UPDATE blog_posts SET title=?,category=?,summary=?,body=?,link_url=?,link_label=?,published=?,updated_at=? WHERE id=?',
                    (data['title'], data['category'], data['summary'], data['body'], data['link_url'], data['link_label'], data['published'], now, post_id))
    else:
        con.execute('INSERT INTO blog_posts(title,category,summary,body,link_url,link_label,published,author_id,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)',
                    (data['title'], data['category'], data['summary'], data['body'], data['link_url'], data['link_label'], data['published'], author_id, now, now))
    con.commit()
