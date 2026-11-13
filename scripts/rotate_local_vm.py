"""Prepare successive single-use Linux lab machines on the operator's computer."""
import argparse
from contextlib import closing, contextmanager
import http.client
import os
from pathlib import Path
import shutil
import sqlite3
import ssl
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.prepare_local_vm import prepare
from scripts.run_local_vm import run


@contextmanager
def operator_lock(database):
    # The OS releases this byte lock if the operator exits unexpectedly. Keep
    # the file in place so simultaneous launches always lock the same object.
    path = database.with_name(database.name + '.rotation.lock')
    with path.open('a+b') as lock:
        try:
            if os.name == 'nt':
                import msvcrt
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise RuntimeError('Outra rotação está em execução para este banco.') from error
        yield


def check_bridge(runtime, port):
    context = ssl.create_default_context(cafile=str(runtime / 'bridge.crt'))
    with closing(http.client.HTTPSConnection('127.0.0.1', port, timeout=5, context=context)) as bridge:
        bridge.request('HEAD', '/api/lab-agent/poll')
        response = bridge.getresponse()
        if response.status != 405 or not response.getheader('Server', '').startswith('PurpleAgentBridge'):
            raise RuntimeError('A porta não respondeu como ponte do laboratório.')


def wait_for_existing(database):
    first_check = time.monotonic()
    announced = False
    while True:
        with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)) as con:
            machines = con.execute("SELECT last_seen FROM remote_machines WHERE status IN ('available','allocated')").fetchall()
        if not machines:
            return
        if not announced:
            print('Aguardando o encerramento das máquinas já cadastradas neste banco.', flush=True)
            announced = True
        if any(seen is not None and time.time() - seen > 180 for (seen,) in machines):
            raise RuntimeError('Existe máquina sem contato. Confira seu supervisor antes de continuar.')
        if time.monotonic() - first_check >= 900 and any(seen is None for (seen,) in machines):
            raise RuntimeError('Existe máquina cadastrada sem primeiro contato. Confira seu supervisor.')
        time.sleep(3)


def rotate(runtime, database, bridge_port, count):
    if not 1 <= count <= 50 or not 1 <= bridge_port <= 65535:
        raise ValueError('Quantidade de 1 a 50 e porta de 1 a 65535 são obrigatórias.')
    if database.is_symlink() or not database.is_file():
        raise ValueError('Selecione um banco existente inicializado pela aplicação.')
    database = database.resolve(strict=True)
    runtime = runtime.resolve(strict=True)
    with operator_lock(database):
        for index in range(count):
            check_bridge(runtime, bridge_port)
            wait_for_existing(database)
            check_bridge(runtime, bridge_port)
            if shutil.disk_usage(runtime).free < 1200 * 1024**2:
                raise RuntimeError('Libere espaço no disco do runtime antes de preparar outra VM.')
            item = prepare(runtime, database, 'Ubuntu local — investigação')
            print(f"Preparando VM {item['machine_id']} ({index + 1}/{count}). Aguarde o contato do agente.", flush=True)
            run(Path(item['folder']) / 'machine.json', runtime, bridge_port=bridge_port, monitor_agent=True)
            print(f"VM {item['machine_id']} encerrada.", flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', required=True, type=Path)
    parser.add_argument('--runtime', required=True, type=Path)
    parser.add_argument('--bridge-port', type=int, default=8443)
    parser.add_argument('--count', type=int, required=True, help='Quantidade máxima de novas VMs nesta rodada.')
    args = parser.parse_args()
    try:
        rotate(args.runtime, args.database, args.bridge_port, args.count)
    except (RuntimeError, OSError, ValueError, sqlite3.Error, http.client.HTTPException) as error:
        parser.exit(1, f'Rotação interrompida: {error}\n')
