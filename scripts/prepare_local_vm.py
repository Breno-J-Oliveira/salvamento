"""Prepare one disposable QEMU guest from locally verified runtime assets."""
import argparse
import base64
import io
import json
from pathlib import Path
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.register_lab_machine import register


def prepare(runtime, database, name):
    runtime = Path(runtime).resolve()
    sys.path.insert(0, str(runtime / 'tools/lib'))
    import pycdlib
    folder = runtime / ('session-' + uuid.uuid4().hex)
    folder.mkdir()
    machine_id = register(database, name, folder / 'agent.token')
    token = (folder / 'agent.token').read_text().strip()

    def entry(path, content, mode='0600'):
        return dict(path=path, content=base64.b64encode(content.encode()).decode(),
                    encoding='b64', owner='root:root', permissions=mode)

    service = '''[Unit]
Description=Purple Talent isolated lab agent
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/purple-agent/lab_agent.py --server https://10.0.2.100:8443 --ca-file /etc/purple-agent/bridge.crt --token-file /etc/purple-agent/token --workspace /srv/purple-lab --run-as purplelab --isolated-lab
Restart=on-failure
RestartSec=5
StandardOutput=journal+console
StandardError=journal+console
[Install]
WantedBy=multi-user.target
'''
    files = [
        entry('/opt/purple-agent/lab_agent.py', (ROOT/'scripts/lab_agent.py').read_text(encoding='utf-8'), '0644'),
        entry('/etc/purple-agent/token', token+'\n'),
        entry('/etc/purple-agent/bridge.crt', (runtime/'bridge.crt').read_text(), '0644'),
        entry('/etc/systemd/system/purple-agent.service', service, '0644')]
    fixtures = {
        'README.txt': 'Caso fictício de acesso fora do expediente. Correlacione access.log, plantao.txt e chamado.txt. Use apenas esta VM. A mentoria acompanha o terminal.\n',
        'access.log': '22:10 login_failed user=ana src=192.0.2.44\n22:14 login_ok user=ana src=192.0.2.44 device=novo\n22:16 export user=ana records=150 request=req-71\n',
        'plantao.txt': 'Ana estava escalada para manutenção das 22h às 23h. A escala não registra autorização de exportação.\n',
        'chamado.txt': 'Chamado fictício SUP-104. Troca de dispositivo solicitada na manhã seguinte. Confirmar com suporte antes de concluir.\n'}
    files.extend(entry('/srv/purple-lab/'+name, content, '0644') for name, content in fixtures.items())
    config = dict(hostname='purple-lab', manage_etc_hosts=True, disable_root=True,
        ssh_pwauth=False, package_update=False, package_upgrade=False,
        users=[], write_files=files,
        runcmd=[['useradd','--create-home','--user-group','--uid','1100','--shell','/bin/bash','purplelab'],
                ['chown','-R','purplelab:purplelab','/srv/purple-lab'],
                ['chmod','700','/srv/purple-lab','/etc/purple-agent'],
                ['systemctl','disable','--now','ssh.service','ssh.socket'],
                ['systemctl','daemon-reload'],
                ['systemctl','enable','--now','purple-agent.service']])
    iso = pycdlib.PyCdlib()
    iso.new(interchange_level=3, joliet=3, rock_ridge='1.09', vol_ident='cidata')
    contents = {'user-data':'#cloud-config\n'+json.dumps(config,ensure_ascii=False),
                'meta-data':json.dumps({'instance-id':folder.name,'local-hostname':'purple-lab'})}
    for index,(filename,content) in enumerate(contents.items()):
        data = content.encode()
        iso.add_fp(io.BytesIO(data),len(data),iso_path=f'/FILE{index}.;1',
                   rr_name=filename,joliet_path='/'+filename)
    iso.write(str(folder/'seed.iso'))
    iso.close()
    subprocess.run([str(runtime/'qemu/qemu-img.exe'),'create','-f','qcow2','-F','qcow2',
                    '-b',str(runtime/'ubuntu-base.img'),str(folder/'disk.qcow2')],
                   check=True,stdout=subprocess.DEVNULL)
    metadata = dict(folder=str(folder),machine_id=machine_id,database=str(Path(database).resolve()))
    (folder/'machine.json').write_text(json.dumps(metadata))
    return metadata


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime',default=str(ROOT/'.runtime/local-vm'))
    parser.add_argument('--database',required=True)
    parser.add_argument('--name',default='Ubuntu local — investigação')
    args = parser.parse_args()
    print(json.dumps(prepare(args.runtime,args.database,args.name)))
