"""Initialize the shared database once before starting the production server."""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
if os.environ.get('PURPLE_ENV') != 'production':
    raise SystemExit('Set PURPLE_ENV=production to start the production server.')

database = Path(os.environ.get('LAB_DATABASE', ''))
if not database.is_absolute() or not database.parent.is_dir():
    raise SystemExit('LAB_DATABASE must point to a file in an existing persistent directory.')
mount = Path(os.environ.get('PERSISTENT_MOUNT', ''))
if not mount.is_absolute() or not os.path.ismount(mount) or mount.resolve() not in database.resolve().parents:
    raise SystemExit('Set PERSISTENT_MOUNT to the mounted disk containing LAB_DATABASE.')

from app import init_db

init_db()
port = int(os.environ.get('PORT', '10000'))
if not 1 <= port <= 65535:
    raise SystemExit('PORT must be between 1 and 65535.')
os.execvp('gunicorn', ['gunicorn', '--bind', f'0.0.0.0:{port}', '--workers', '1',
                       '--threads', '4', '--timeout', '60', 'app:app'])
