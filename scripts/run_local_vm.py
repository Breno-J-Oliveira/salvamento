"""Supervise one prepared local QEMU VM, with loopback gateway and disk reserve."""
import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from remote_labs import finish_session


def retire(database, machine_id):
    with closing(sqlite3.connect(database, timeout=10)) as con, con:
        con.row_factory = sqlite3.Row
        con.execute('BEGIN IMMEDIATE')
        for active in con.execute("SELECT * FROM remote_sessions WHERE machine_id=? AND status='active'",
                                  (machine_id,)).fetchall():
            finish_session(con, active, int(time.time()), 'ended')
        con.execute("UPDATE remote_machines SET status='retired' WHERE id=?", (machine_id,))


def run(metadata, runtime=None):
    item = json.loads(Path(metadata).read_text(encoding='utf-8-sig'))
    runtime = Path(runtime if runtime is not None else ROOT/'.runtime/local-vm').resolve(strict=True)
    folder = Path(item['folder']).resolve()
    if folder.parent != runtime or not folder.name.startswith('session-') or not folder.is_dir():
        raise ValueError('Unexpected VM directory.')
    executable = runtime/'qemu/qemu-system-x86_64.exe'
    database = Path(item['database'])
    if database.is_symlink():
        raise ValueError('The database must be a regular file, not a symbolic link.')
    database = database.resolve(strict=True)
    machine_id = item['machine_id']
    assets = [executable, folder/'disk.qcow2', folder/'seed.iso']
    if not isinstance(machine_id, int) or isinstance(machine_id, bool) or machine_id <= 0:
        raise ValueError('Invalid machine identifier.')
    if not database.is_file() or any(not path.is_file() or path.is_symlink() for path in assets):
        raise ValueError('Prepared VM assets are missing or invalid.')
    with closing(sqlite3.connect(database.as_uri()+'?mode=ro', uri=True)) as con:
        row = con.execute('SELECT status FROM remote_machines WHERE id=?', (machine_id,)).fetchone()
    if not row or row[0] != 'available':
        raise ValueError('A fresh available machine is required.')
    # Single-use reservation precedes the cleanup scope. A second supervisor must
    # never retire the executor owned by the first, even before its first poll.
    try:
        with (folder/'supervisor.lock').open('x', encoding='utf-8') as lock:
            json.dump({'supervisor_pid':os.getpid(), 'machine_id':machine_id,
                       'reserved_at':int(time.time())}, lock)
    except FileExistsError:
        raise ValueError('A supervisor reservation already exists. Inspect its logs and prepare a fresh VM; do not remove an active reservation.') from None
    def option(path):
        return str(path).replace(',', ',,')
    args = [str(executable), '-name','Purple-Talent-Linux', '-machine','q35',
        '-accel','tcg,thread=multi','-cpu','max','-smp','2','-m','1024',
        '-display','none','-monitor','none','-vga','none',
        '-serial','file:'+str(folder/'serial.log'),
        '-drive','file='+option(folder/'disk.qcow2')+',if=virtio,format=qcow2,throttling.bps-write=10485760',
        '-drive','file='+option(folder/'seed.iso')+',if=virtio,format=raw,readonly=on',
        '-smbios','type=1,serial=ds=nocloud',
        '-netdev','user,id=lab,restrict=on,ipv6=off,guestfwd=tcp:10.0.2.100:8443-tcp:127.0.0.1:8443,,reconnect-ms=500',
        '-device','virtio-net-pci,netdev=lab','-no-reboot']
    process = None
    try:
        if shutil.disk_usage(runtime).free < 1200*1024**2:
            raise ValueError('Insufficient disk space to start a VM safely.')
        with (folder/'qemu.stderr.log').open('w') as errors:
            process = subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                stderr=errors,creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            (folder/'process.json').write_text(json.dumps({'pid':process.pid}))
            print('Linux VM started. Machine '+str(machine_id),flush=True)
            while process.poll() is None:
                if shutil.disk_usage(runtime).free < 1200*1024**2:
                    print('VM stopped to preserve Windows disk space.',flush=True)
                    break
                with closing(sqlite3.connect(database.as_uri()+'?mode=ro',uri=True)) as con:
                    row = con.execute('SELECT status FROM remote_machines WHERE id=?',(machine_id,)).fetchone()
                if not row or row[0]=='retired':
                    print('Session ended. VM stopped; prepare a fresh VM for the next participant.',flush=True)
                    break
                time.sleep(3)
    finally:
        try:
            if process is not None:
                if process.poll() is None:
                    process.terminate()
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=15)
        finally:
            retire(database, machine_id)
    return process.returncode


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metadata',required=True)
    parser.add_argument('--runtime',default=str(ROOT/'.runtime/local-vm'),help='Explicit runtime directory, including when stored on another disk.')
    args=parser.parse_args()
    run(args.metadata, args.runtime)
