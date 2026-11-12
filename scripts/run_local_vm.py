"""Supervise one prepared local QEMU VM, with loopback gateway and disk reserve."""
import argparse
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from remote_labs import finish_session


def run(metadata):
    item = json.loads(Path(metadata).read_text(encoding='utf-8-sig'))
    runtime = (ROOT/'.runtime/local-vm').resolve()
    folder = Path(item['folder']).resolve()
    if folder.parent != runtime or not folder.name.startswith('session-'):
        raise ValueError('Unexpected VM directory.')
    executable = runtime/'qemu/qemu-system-x86_64.exe'
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
    with (folder/'qemu.stderr.log').open('w') as errors:
        process = subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
            stderr=errors,creationflags=subprocess.CREATE_NO_WINDOW)
        (folder/'process.json').write_text(json.dumps({'pid':process.pid}))
        print('Linux VM started. Machine '+str(item['machine_id']),flush=True)
        try:
            while process.poll() is None:
                if shutil.disk_usage(runtime).free < 1200*1024**2:
                    print('VM stopped to preserve Windows disk space.',flush=True)
                    break
                with sqlite3.connect(Path(item['database']).as_uri()+'?mode=ro',uri=True) as con:
                    row = con.execute('SELECT status FROM remote_machines WHERE id=?',(item['machine_id'],)).fetchone()
                if not row or row[0]=='retired':
                    print('Session ended. VM stopped; prepare a fresh VM for the next participant.',flush=True)
                    break
                time.sleep(3)
        finally:
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=15)
            with sqlite3.connect(item['database'], timeout=10) as con:
                con.row_factory = sqlite3.Row
                con.execute('BEGIN IMMEDIATE')
                for active in con.execute("SELECT * FROM remote_sessions WHERE machine_id=? AND status='active'",
                                          (item['machine_id'],)).fetchall():
                    finish_session(con, active, int(time.time()), 'ended')
                con.execute("UPDATE remote_machines SET status='retired' WHERE id=?", (item['machine_id'],))
        return process.returncode


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metadata',required=True)
    args=parser.parse_args()
    run(args.metadata)
