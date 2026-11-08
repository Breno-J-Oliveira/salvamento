"""Ambiente fictício de observação, sem acesso ao servidor real da plataforma."""
import os
import re

from flask import Flask, abort, render_template_string

app = Flask(__name__)
flag = os.environ['FLAG']
if not re.fullmatch(r'CTF\{[a-f0-9]{16,64}\}', flag):
    raise ValueError('Configuração de ambiente inválida')
source_ip = f'192.0.2.{1 + int(flag[4:6], 16) % 254}'

# Registros sintéticos e endereços reservados para documentação. Nenhum dado é
# obtido do host; o quadro é uma captura fixa, não um ataque em tempo real.
PAGES = {
    'overview': ('Visão geral', 'Estado da captura', [
        ('Servidor', 'atlas-web-01'), ('Ambiente', 'Produção simulada'),
        ('Janela de observação', '14:00–14:15 UTC'), ('Disponibilidade', 'Operacional'),
        ('Serviço web', 'Ativo'), ('Fila de exportação', 'Ativa'),
    ]),
    'access': ('Acessos HTTP', 'Acessos registrados', [
        ('14:01:12', '203.0.113.18 | GET /health | 200 | req-a01'),
        ('14:03:04', f'{source_ip} | POST /session | 401 | req-b11'),
        ('14:03:19', f'{source_ip} | POST /session | 401 | req-b12'),
        ('14:04:02', '203.0.113.33 | GET /dashboard | 200 | req-c01'),
        ('14:05:17', f'{source_ip} | POST /session | 200 | req-b13'),
        ('14:06:09', f'{source_ip} | GET /api/reports/export | 200 | req-b14'),
        ('14:06:12', '203.0.113.18 | GET /health | 200 | req-a02'),
        ('14:08:33', '203.0.113.33 | GET /reports | 200 | req-c02'),
        ('14:10:20', f'{source_ip} | GET /api/reports/export | 200 | req-b15'),
    ]),
    'events': ('Eventos', 'Eventos do sistema', [
        ('14:00:00', 'Serviço web iniciado | host=atlas-web-01'),
        ('14:03:04', 'Autenticação recusada | conta=svc-report | req-b11'),
        ('14:03:19', 'Autenticação recusada | conta=svc-report | req-b12'),
        ('14:05:17', 'Sessão criada | conta=svc-report | req-b13'),
        ('14:06:09', 'Exportação solicitada | conta=svc-report | req-b14'),
        ('14:06:10', 'Leitura de registros | coleção=clientes | volume=5000 | req-b14'),
        ('14:10:20', 'Exportação solicitada | conta=svc-report | req-b15'),
        ('14:10:21', 'Leitura de registros | coleção=clientes | volume=5000 | req-b15'),
        ('14:12:00', 'Verificação de integridade concluída | resultado=ok'),
    ]),
    'processes': ('Processos', 'Processos observados', [
        ('web-gateway', 'pid=172 | usuário=web | estado=ativo | iniciado=14:00:00'),
        ('report-worker', 'pid=184 | usuário=reports | estado=ativo | iniciado=14:00:01'),
        ('integrity-check', 'pid=215 | usuário=monitor | estado=concluído | iniciado=14:11:59'),
        ('audit-agent', 'pid=167 | usuário=monitor | estado=ativo | iniciado=13:58:01'),
    ]),
}

TEMPLATE = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{{ title }} · Atlas Monitor</title>
<style>
:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#100e1a;color:#f2eefb;font:16px system-ui,sans-serif;line-height:1.5}
header{border-bottom:1px solid #393046;background:#171321}header div,main{max-width:1100px;margin:auto;padding:20px 24px}.brand{font-weight:750;letter-spacing:.04em}header small{display:block;color:#b9aacd}
nav{display:flex;gap:8px;flex-wrap:wrap;margin-top:18px}nav a{color:#d9c5f4;padding:8px 12px;border-radius:7px;text-decoration:none}nav a[aria-current]{background:#51347a;color:#fff}a:focus-visible{outline:3px solid #d7baff;outline-offset:3px}
h1{font-size:clamp(1.7rem,4vw,2.4rem);margin:0 0 8px}p{color:#c9bed7}.panel{margin-top:24px;border:1px solid #453a56;border-radius:12px;background:#1a1625;overflow:hidden}.panel h2{font-size:1.1rem;margin:0;padding:20px 20px 12px}.table-wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;min-width:620px}th,td{text-align:left;padding:13px 20px;border-top:1px solid #383040;vertical-align:top}th{color:#c7b7da;font-size:.85rem}td:first-child{white-space:nowrap;color:#d8c6f4}td:nth-child(2){overflow-wrap:anywhere}footer{max-width:1100px;margin:auto;padding:12px 24px 32px;color:#ac9dbd;font-size:.85rem}
</style></head><body><header><div><span class="brand">ATLAS MONITOR</span><small>Console de observação · atlas-web-01</small>
<nav aria-label="Seções do servidor">{% for key, page in pages.items() %}<a href="{{ '/' if key == 'overview' else '/' ~ key }}" {% if key == current %}aria-current="page"{% endif %}>{{ page[0] }}</a>{% endfor %}</nav></div></header>
<main><h1>{{ title }}</h1><p>Captura de um ambiente fictício. Horários exibidos em UTC.</p>
<section class="panel"><h2>{{ heading }}</h2><div class="table-wrap" role="region" aria-label="{{ heading }}" tabindex="0"><table><thead><tr><th scope="col">{{ 'Indicador' if current == 'overview' else ('Processo' if current == 'processes' else 'Horário') }}</th><th scope="col">Registro</th></tr></thead><tbody>{% for label, value in rows %}<tr><td>{{ label }}</td><td>{{ value }}</td></tr>{% endfor %}</tbody></table></div></section></main><footer>Ambiente de treinamento isolado · dados fictícios</footer></body></html>"""


@app.after_request
def security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Cache-Control'] = 'no-store'
    return response


@app.get('/health')
def health():
    return {'status': 'ok'}


@app.get('/')
@app.get('/<page>')
def show(page='overview'):
    if page not in PAGES:
        abort(404)
    title, heading, rows = PAGES[page]
    return render_template_string(TEMPLATE, title=title, heading=heading,
                                  rows=rows, current=page, pages=PAGES)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
