"""Verified SQLite snapshot and restore into a new, explicitly named file."""
import argparse
from contextlib import closing
from pathlib import Path
import sqlite3
import time


def copy_verified(source, destination):
    source = Path(source).resolve(strict=True)
    destination = Path(destination).resolve()
    if not source.is_file():
        raise ValueError('A origem deve ser um arquivo SQLite existente.')
    if source == destination:
        raise ValueError('Origem e destino devem ser diferentes.')
    # Exclusive reservation rejects existing files and symlinks; never overwrite.
    with destination.open('xb'):
        pass
    try:
        deadline = time.monotonic() + 30

        def progress(status, remaining, total):
            if time.monotonic() > deadline:
                raise TimeoutError('O banco não ficou disponível para cópia em 30 segundos.')

        with closing(sqlite3.connect(source.as_uri() + '?mode=ro', uri=True, timeout=5)) as origin:
            with closing(sqlite3.connect(destination)) as target:
                origin.backup(target, pages=256, progress=progress, sleep=0.1)
                if target.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
                    raise ValueError('A verificação de integridade da cópia falhou.')
        return destination
    except BaseException:
        destination.unlink(missing_ok=True)
        raise


def main():
    parser = argparse.ArgumentParser(description='Copiar ou restaurar SQLite para um novo arquivo, com verificação de integridade.')
    parser.add_argument('operation', choices=['backup', 'restore'])
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    try:
        result = copy_verified(args.source, args.destination)
    except (OSError, sqlite3.Error, ValueError, TimeoutError):
        parser.exit(1, 'A operação falhou. Confira origem, destino, espaço e permissões; nenhum arquivo existente é sobrescrito.\n')
    print(f'{args.operation}: cópia verificada em {result}')


if __name__ == '__main__':
    main()
