"""Register one disposable machine and write its token to a NEW private file."""
import argparse
from contextlib import closing
import hashlib
import os
from pathlib import Path
import secrets
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def register(database, name, token_file):
    import remote_labs
    source = Path(database)
    destination = Path(token_file)
    name = name.strip()
    if not source.is_file() or source.is_symlink():
        raise ValueError('Database must already exist and must be a regular file.')
    if not 1 <= len(name) <= 100:
        raise ValueError('Machine name must contain 1 to 100 characters.')
    if not destination.is_absolute() or not destination.parent.is_dir():
        raise ValueError('Use an absolute token path in an existing private directory.')
    token = secrets.token_urlsafe(48)
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as secret_file:
            secret_file.write(token + '\n')
            secret_file.flush()
            os.fsync(secret_file.fileno())
        with closing(sqlite3.connect(source)) as con:
            with con:
                remote_labs.migrate(con)
                identifier = con.execute(
                    "INSERT INTO remote_machines(name,token_hash,status,last_seen) VALUES(?,?,'available',NULL)",
                    (name, hashlib.sha256(token.encode()).hexdigest())).lastrowid
        return identifier
    except BaseException:
        # This file was created by this invocation only. Never remove prior files.
        destination.unlink(missing_ok=True)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--token-file', required=True)
    args = parser.parse_args()
    try:
        identifier = register(args.database, args.name, args.token_file)
    except (ValueError, OSError, sqlite3.Error) as exc:
        parser.error('Registration failed: ' + type(exc).__name__)
    print(f'Machine {identifier} registered. Private token file: {Path(args.token_file)}')
    print('Transfer the file securely to the VM, owned by root with mode 0600. Never commit it.')


if __name__ == '__main__':
    main()
