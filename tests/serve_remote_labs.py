"""Disposable HTTP fixture for remote-lab protocol QA. No commands are executed."""
import hashlib
import os
from pathlib import Path
import sqlite3
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ['SECRET_KEY'] = 'remote-browser-fixture-only'
from scripts.prepare_demo import prepare_demo
import app

if __name__ == '__main__':
    target = ROOT / 'output' / 'qa'
    target.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='remote-browser-', dir=target) as folder:
        app.DB = str(prepare_demo(Path(folder) / 'fixture.db'))
        with sqlite3.connect(app.DB) as con:
            for mid in (1, 2):
                token = 'browser-fixture-agent-' + str(mid) + '-' + 'x' * 32
                con.execute('INSERT INTO remote_machines(name,token_hash) VALUES(?,?)',
                            ('Executor fictício QA ' + str(mid), hashlib.sha256(token.encode()).hexdigest()))
        app.app.run(host='127.0.0.1', port=5071, debug=False, use_reloader=False)
