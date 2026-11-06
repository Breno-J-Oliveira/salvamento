"""Servidor de QA com banco separado; nunca usa lab.db da equipe."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('SECRET_KEY', 'isolated-browser-test-key-not-for-real-use')
import app

target = ROOT / 'output' / 'qa'
target.mkdir(parents=True, exist_ok=True)
app.DB = str(target / 'browser.db')
app.init_db()
app.app.run(host='127.0.0.1', port=5055, debug=False, use_reloader=False)
