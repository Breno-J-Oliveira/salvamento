"""Read-only validation of a disposable demonstration database."""
import argparse
from contextlib import closing
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.prepare_demo import DEMO_MARKER


def verify_demo(database):
    source=Path(database)
    if source.is_symlink() or not source.is_file() or source.name.lower()=='lab.db':
        raise ValueError('Use an existing demonstration database.')
    with closing(sqlite3.connect(source.resolve().as_uri()+'?mode=ro',uri=True)) as con:
        if con.execute("SELECT value FROM demo_metadata WHERE name=?",('fixture',)).fetchone() != (DEMO_MARKER,):
            raise ValueError('Database is not a recognized demonstration fixture.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('database')
    args=parser.parse_args()
    try:
        verify_demo(args.database)
    except (OSError,ValueError,sqlite3.Error):
        parser.exit(1,'Base de demonstracao nao reconhecida. Nenhuma alteracao aplicada.\n')
