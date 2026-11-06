"""Servidor isolado de QA para recrutamento, sem Docker nem banco da equipe."""
import os
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('SECRET_KEY', 'recruitment-browser-qa-only-key')
import app

target = ROOT / 'output' / 'qa'
target.mkdir(parents=True, exist_ok=True)
app.DB = str(target / 'recruitment-browser.db')
app.init_db()
connection = sqlite3.connect(app.DB)
try:
    with connection:
        for title, side in [('DEMO QA — SOC Júnior', 'Blue Team'), ('DEMO QA — Estágio AppSec', 'Red Team')]:
            connection.execute('''INSERT INTO jobs(title,company,description,side,min_points,active,created_by,created_at)
                SELECT ?, 'Empresa fictícia de QA', 'Oportunidade sintética para verificar o fluxo sem dados reais.', ?, 0,1,1,?
                WHERE NOT EXISTS (SELECT 1 FROM jobs WHERE title=?)''', (title, side, int(time.time()), title))
finally:
    connection.close()
app.app.run(host='127.0.0.1', port=5056, debug=False, use_reloader=False)
